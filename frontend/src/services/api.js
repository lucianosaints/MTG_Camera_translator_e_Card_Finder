/**
 * MTG Translator — Serviço de API
 *
 * Comunicação com o backend Django.
 * Nenhuma chave de API é exposta aqui — toda comunicação
 * externa passa pelo backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Envia uma imagem de carta para identificação no backend.
 *
 * @param {File} imageFile - Arquivo de imagem (JPEG ou PNG)
 * @returns {Promise<Object>} Dados da carta identificada
 * @throws {Error} Em caso de erro de rede ou resposta inválida
 */
export async function identifyCard(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);

  try {
    const token = localStorage.getItem('access_token');
    const headers = {
      'Accept': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/cards/identify/`, {
      method: 'POST',
      headers: headers,
      body: formData,
      // Não definir Content-Type — o browser seta automaticamente
      // com o boundary correto para multipart/form-data
    });

    const data = await response.json();

    // Erro HTTP (4xx, 5xx)
    if (!response.ok) {
      const errorMessage =
        (typeof data?.error === 'string' ? data.error : data?.error?.message) ||
        data?.detail ||
        'Erro desconhecido ao processar a imagem.';
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    // Erro de rede (sem conexão, CORS, etc.)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        'Não foi possível conectar ao servidor. Verifique se o backend está rodando.'
      );
    }
    throw error;
  }
}
