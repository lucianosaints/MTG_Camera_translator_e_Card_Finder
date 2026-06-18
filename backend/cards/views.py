"""
MTG Translator — Views

Endpoint principal: POST /api/v1/cards/identify/
Recebe imagem -> Valida -> IA identifica -> Scryfall busca -> Retorna JSON

Segurança aplicada:
- Validação rigorosa de upload (validators.py)
- Rate limiting (throttles.py)
- Tratamento seguro de erros (exceptions.py)
- Logging interno (nunca expõe detalhes ao cliente)
"""
import logging

from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.timezone import now
from django.contrib.auth.models import User

from .models import CardScan
from .serializers import CardIdentifyRequestSerializer
from .throttles import CardIdentifyThrottle, CardIdentifyBurstThrottle
from .validators import validate_image_file, sanitize_filename
from .services.vision_service import (
    VisionService,
    VisionServiceError,
    VisionServiceUnavailable,
    VisionServiceQuotaExceeded,
)
from .services.scryfall_service import (
    ScryfallService,
    ScryfallCardNotFound,
    ScryfallServiceUnavailable,
    ScryfallServiceError,
)

logger = logging.getLogger('cards')


class CardIdentifyView(APIView):
    """
    POST /api/v1/cards/identify/

    Endpoint principal para identificação de cartas MTG.

    Fluxo:
    1. Recebe imagem via multipart/form-data (campo 'image')
    2. Valida tipo, tamanho e integridade do arquivo
    3. Envia para IA de Visão (OpenRouter) para identificação
    4. Busca dados oficiais no Scryfall
    5. Retorna JSON com dados da carta traduzidos

    Rate Limiting:
    - 10 requisições/minuto por IP (sustentado)
    - 3 requisições/segundo por IP (burst)
    """

    parser_classes = [MultiPartParser]
    throttle_classes = [CardIdentifyThrottle, CardIdentifyBurstThrottle]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Processa upload de imagem e retorna dados da carta identificada.

        Request:
            multipart/form-data com campo 'image' (JPEG ou PNG, max 5MB)

        Response (200 — Carta identificada):
            {
                "success": true,
                "identified": true,
                "card": { ... dados da carta ... }
            }

        Response (200 — Carta não identificada):
            {
                "success": true,
                "identified": false,
                "card": null,
                "message": "Não foi possível identificar..."
            }

        Response (400 — Validação falhou):
            {
                "success": false,
                "error": { "code": 400, "message": "..." }
            }

        Response (503 — Serviço indisponível):
            {
                "success": false,
                "error": { "code": 503, "message": "..." }
            }
        """
        # ── 1. Validar entrada com serializer ──
        serializer = CardIdentifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['image']

        # ── 1.5. Validar limites da conta (Freemium) ──
        user = request.user
        if hasattr(user, 'profile') and not user.profile.is_premium:
            profile = user.profile
            hoje = now().date()
            if profile.last_scan_date != hoje:
                profile.scans_today = 0
                profile.last_scan_date = hoje
                
            if profile.scans_today >= 10:
                logger.warning('Usuário free %s atingiu o limite de scans.', user.username)
                return Response(
                    {'error': 'LIMIT_REACHED'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Incrementar uso
        if hasattr(user, 'profile') and not user.profile.is_premium:
            user.profile.scans_today += 1
            user.profile.save()

        # ── 2. Validação de segurança aprofundada ──
        validate_image_file(uploaded_file)

        # ── 3. Sanitizar nome do arquivo ──
        uploaded_file.name = sanitize_filename(uploaded_file.name)

        # ── 4. Ler bytes da imagem ──
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()
        content_type = uploaded_file.content_type or 'image/jpeg'

        logger.info(
            'Nova requisição de identificação — arquivo: %s, tamanho: %d bytes',
            uploaded_file.name, len(image_bytes)
        )

        # ── 5. Criar registro de scan (para auditoria) ──
        uploaded_file.seek(0)
        scan = CardScan.objects.create(original_image=uploaded_file)

        # ── 6. Identificar carta via IA de Visão ──
        try:
            vision_service = VisionService()
            card_name = vision_service.identify_card(image_bytes, content_type)
        except VisionServiceQuotaExceeded as exc:
            logger.warning('Cota da IA excedida: %s', exc)
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 503,
                        'message': str(exc),
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except VisionServiceUnavailable as exc:
            logger.error('IA de visão indisponível: %s', exc)
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 503,
                        'message': str(exc),
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except VisionServiceError as exc:
            logger.error('Erro no serviço de visão: %s', exc)
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 500,
                        'message': 'Erro ao processar a imagem. Tente novamente.',
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── 7. Carta não identificada ──
        if card_name is None:
            scan.identified = False
            scan.save(update_fields=['identified'])

            logger.info('Carta não identificada no scan #%d', scan.pk)

            return Response(
                {
                    'success': True,
                    'identified': False,
                    'card': None,
                    'message': (
                        'Não foi possível identificar a carta na imagem. '
                        'Tente tirar uma foto mais nítida com boa iluminação.'
                    ),
                },
                status=status.HTTP_200_OK,
            )

        # ── 8. Atualizar scan com nome da IA ──
        scan.card_name_en = card_name
        scan.raw_ai_response = card_name
        scan.save(update_fields=['card_name_en', 'raw_ai_response'])

        # ── 9. Buscar dados no Scryfall ──
        try:
            scryfall_service = ScryfallService()
            card_data = scryfall_service.search_card(card_name)
        except ScryfallCardNotFound:
            scan.identified = False
            scan.save(update_fields=['identified'])

            logger.info(
                'Carta identificada como "%s" mas não encontrada no Scryfall',
                card_name
            )

            return Response(
                {
                    'success': True,
                    'identified': False,
                    'card': None,
                    'message': (
                        f'A IA identificou o texto "{card_name}", mas não foi '
                        f'encontrada uma carta correspondente no banco de dados. '
                        f'Tente uma foto com melhor enquadramento.'
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except ScryfallServiceUnavailable as exc:
            logger.error('Scryfall indisponível: %s', exc)
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 503,
                        'message': str(exc),
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ScryfallServiceError as exc:
            logger.error('Erro no serviço Scryfall: %s', exc)
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 500,
                        'message': 'Erro ao buscar dados da carta. Tente novamente.',
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── 10. Atualizar scan com dados completos ──
        scan.identified = True
        scan.card_name_pt = card_data.get('name_pt', '')
        scan.scryfall_id = card_data.get('scryfall_id', '')
        scan.save(update_fields=['identified', 'card_name_pt', 'scryfall_id'])

        logger.info(
            'Carta identificada com sucesso: %s (%s) — scan #%d',
            card_data.get('name_en'), card_data.get('name_pt'), scan.pk
        )

        # ── 11. Retornar resposta de sucesso ──
        return Response(
            {
                'success': True,
                'identified': True,
                'card': card_data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """
    POST /api/v1/register/
    Permite o cadastro de novos usuários. O UserProfile será criado automaticamente por signals.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Cria o usuário. O signal (post_save) criará o UserProfile.
        user = User.objects.create_user(username=username, email=email, password=password)
        
        return Response(
            {
                'success': True, 
                'message': 'User created successfully',
                'user': {
                    'username': user.username,
                    'email': user.email
                }
            }, 
            status=status.HTTP_201_CREATED
        )
