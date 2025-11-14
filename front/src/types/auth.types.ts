// src/types/auth.types.ts
export interface IRegisterRequest {
  login: string;
  password: string;
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