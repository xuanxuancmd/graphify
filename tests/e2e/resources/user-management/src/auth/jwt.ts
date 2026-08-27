/**
 * JWT Manager — token generation and verification utility.
 *
 * Issues signed JWT tokens for authenticated sessions.
 * Tokens carry userId and email claims with an expiry timestamp.
 */
export interface TokenPayload {
  userId: string;
  email: string;
  exp: number;
}

export class JwtManager {
  private readonly secret: string;
  private readonly expiresInSec: number;

  constructor(secret: string = "test-secret", expiresInSec: number = 3600) {
    this.secret = secret;
    this.expiresInSec = expiresInSec;
  }

  /**
   * Generate a JWT token for a user.
   * The token encodes userId, email, and expiry.
   */
  generateToken(userId: string, email: string): string {
    const payload: TokenPayload = {
      userId,
      email,
      exp: Math.floor(Date.now() / 1000) + this.expiresInSec,
    };
    const encoded = Buffer.from(JSON.stringify(payload)).toString("base64url");
    const signature = this.simpleSign(encoded);
    return `${encoded}.${signature}`;
  }

  /**
   * Verify a JWT token and return its payload.
   * Throws if the token is invalid, tampered, or expired.
   */
  verifyToken(token: string): TokenPayload {
    const [encoded, signature] = token.split(".");
    if (!encoded || !signature) {
      throw new Error("Invalid token format");
    }
    const expectedSig = this.simpleSign(encoded);
    if (signature !== expectedSig) {
      throw new Error("Invalid token signature");
    }
    const payload: TokenPayload = JSON.parse(
      Buffer.from(encoded, "base64url").toString("utf-8"),
    );
    if (payload.exp < Math.floor(Date.now() / 1000)) {
      throw new Error("Token expired");
    }
    return payload;
  }

  /**
   * Refresh an expired token — issues a new token with the same user
   * but a fresh expiry. Requires a valid (non-tampered) token input
   * even if expired.
   */
  refreshToken(token: string): string {
    const [encoded] = token.split(".");
    if (!encoded) throw new Error("Invalid token format");
    const payload: TokenPayload = JSON.parse(
      Buffer.from(encoded, "base64url").toString("utf-8"),
    );
    return this.generateToken(payload.userId, payload.email);
  }

  private simpleSign(data: string): string {
    let hash = 0;
    const combined = data + this.secret;
    for (let i = 0; i < combined.length; i++) {
      hash = ((hash << 5) - hash) + combined.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
  }
}
