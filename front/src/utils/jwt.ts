export const decodeToken = (token: string): any => {
  try {
    const [, payloadBase64] = token.split("."); 
    
    if (!payloadBase64) {
      throw new Error("Invalid JWT format: missing payload");
    }

    return JSON.parse(atob(payloadBase64));
  } catch (e) {
    console.error("Ошибка декодирования токена:", e);
    return null;
  }
};