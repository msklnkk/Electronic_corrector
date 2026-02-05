// src/types/auth.types.ts
export interface IRegisterRequest {
  first_name: string;
  surname_name: string;
  patronomic_name: string | null;        
  login: string;                  
  password: string;
  tg_username: string;               
}

export interface IToken {
  access_token: string;
  token_type: string;
}

export interface IClientResponse {
  clientid?: number;
  login?: string;
  [key: string]: any;
}