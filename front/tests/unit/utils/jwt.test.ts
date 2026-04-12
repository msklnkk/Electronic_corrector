// tests/unit/utils/jwt.test.ts
import { decodeToken } from '../../../src/utils/jwt';

describe('decodeToken', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('должен декодировать корректный JWT токен', () => {
    // Base64 encoded payload: {"user_id":1,"email":"test@example.com","role":"user"}
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJyb2xlIjoidXNlciJ9.signature';
    
    const decoded = decodeToken(token);

    expect(decoded).toEqual({
      user_id: 1,
      email: 'test@example.com',
      role: 'user'
    });
  });

  it('должен возвращать null при некорректном формате токена', () => {
    const invalidToken = 'invalid.token';
    const decoded = decodeToken(invalidToken);

    expect(decoded).toBeNull();
  });

  it('должен возвращать null при пустой строке', () => {
    const decoded = decodeToken('');

    expect(decoded).toBeNull();
  });

  it('должен обрабатывать токены без правильных точек', () => {
    const token = 'onlyonepart';
    const decoded = decodeToken(token);

    expect(decoded).toBeNull();
  });

  it('должен декодировать токен с дополнительными полями', () => {
    // Base64 encoded payload: {"sub":"user:1","email":"test@example.com","iat":1234567890,"exp":1234571490}
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyOjEiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJpYXQiOjEyMzQ1Njc4OTAsImV4cCI6MTIzNDU3MTQ5MH0.signature';
    
    const decoded = decodeToken(token);

    expect(decoded).toEqual({
      sub: 'user:1',
      email: 'test@example.com',
      iat: 1234567890,
      exp: 1234571490
    });
  });
});
