/**
 * Password Hasher — security utility for password hashing and verification.
 *
 * Uses bcrypt-style salted hashing (simulated for test fixture).
 */
export class PasswordHasher {
  private readonly saltRounds: number;

  constructor(saltRounds: number = 10) {
    this.saltRounds = saltRounds;
  }

  /**
   * Hash a plaintext password.
   * Enforces minimum length of 8 characters.
   */
  hash(plaintext: string): string {
    if (plaintext.length < 8) {
      throw new Error("Password must be at least 8 characters");
    }
    // Simulated hash — real implementation would use bcrypt
    return `$2b$${this.saltRounds}$${this.simpleHash(plaintext)}`;
  }

  /**
   * Verify a plaintext password against a stored hash.
   */
  verify(plaintext: string, hash: string): boolean {
    if (plaintext.length < 8) return false;
    const expected = `$2b$${this.saltRounds}$${this.simpleHash(plaintext)}`;
    return hash === expected;
  }

  private simpleHash(input: string): string {
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36).padStart(22, "0");
  }
}
