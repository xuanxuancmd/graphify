/**
 * Auth Service — application service for authentication operations.
 *
 * Orchestrates user registration, login, and token refresh flows.
 * Collaborates with UserRepository, PasswordHasher, and JwtManager.
 */
import { User, Profile } from "../models/user.ts";
import { UserRepository } from "../repositories/user.repository.ts";
import { PasswordHasher } from "./password.ts";
import { JwtManager } from "./jwt.ts";

export interface AuthResult {
  user: User;
  token: string;
}

export class AuthService {
  private readonly userRepo: UserRepository;
  private readonly passwordHasher: PasswordHasher;
  private readonly jwtManager: JwtManager;

  constructor(
    userRepo: UserRepository,
    passwordHasher: PasswordHasher,
    jwtManager: JwtManager,
  ) {
    this.userRepo = userRepo;
    this.passwordHasher = passwordHasher;
    this.jwtManager = jwtManager;
  }

  /**
   * Register a new user — creates the user account and returns auth token.
   * Email must not already be registered (enforced by UserRepository).
   */
  register(
    email: string,
    password: string,
    displayName: string,
  ): AuthResult {
    const existing = this.userRepo.findByEmail(email);
    if (existing) {
      throw new Error("Email already registered");
    }
    const passwordHash = this.passwordHasher.hash(password);
    const userId = this.generateUserId();
    const profile = new Profile(displayName);
    const user = User.register(userId, email, passwordHash, profile);
    this.userRepo.save(user);
    const token = this.jwtManager.generateToken(user.id, user.email);
    return { user, token };
  }

  /**
   * Login — verifies credentials and returns auth token.
   * User must be active; suspended or deleted users cannot log in.
   */
  login(email: string, password: string): AuthResult {
    const user = this.userRepo.findByEmail(email);
    if (!user) {
      throw new Error("User not found");
    }
    if (user.status !== "active") {
      throw new Error(`User account is ${user.status}`);
    }
    const valid = this.passwordHasher.verify(password, user.passwordHash);
    if (!valid) {
      throw new Error("Invalid password");
    }
    const token = this.jwtManager.generateToken(user.id, user.email);
    return { user, token };
  }

  /**
   * Refresh an expired token — issues a new token from a valid-but-expired one.
   */
  refreshToken(token: string): string {
    return this.jwtManager.refreshToken(token);
  }

  private generateUserId(): string {
    return `user_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }
}
