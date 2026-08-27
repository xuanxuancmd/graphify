/**
 * User Service — application service for user management operations.
 *
 * Orchestrates CRUD operations on User aggregates through the repository.
 * Separated from AuthService which handles authentication concerns.
 */
import { User, Profile } from "../models/user.ts";
import { UserRepository } from "../repositories/user.repository.ts";

export class UserService {
  private readonly userRepo: UserRepository;

  constructor(userRepo: UserRepository) {
    this.userRepo = userRepo;
  }

  /**
   * Create a new user — used by admin/CLI flows (not self-registration).
   * Self-registration goes through AuthService.register().
   */
  createUser(
    email: string,
    passwordHash: string,
    displayName: string,
  ): User {
    const existing = this.userRepo.findByEmail(email);
    if (existing) {
      throw new Error("Email already registered");
    }
    const userId = `user_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const profile = new Profile(displayName);
    const user = User.register(userId, email, passwordHash, profile);
    this.userRepo.save(user);
    return user;
  }

  /**
   * Get a user by ID.
   */
  getUser(id: string): User {
    const user = this.userRepo.findById(id);
    if (!user) {
      throw new Error("User not found");
    }
    return user;
  }

  /**
   * Update a user's profile information.
   */
  updateUser(
    id: string,
    displayName?: string,
    avatarUrl?: string,
    bio?: string,
  ): User {
    const user = this.userRepo.findById(id);
    if (!user) {
      throw new Error("User not found");
    }
    const profile = new Profile(
      displayName ?? user.profile.displayName,
      avatarUrl ?? user.profile.avatarUrl,
      bio ?? user.profile.bio,
    );
    user.updateProfile(profile);
    this.userRepo.save(user);
    return user;
  }

  /**
   * Suspend a user — blocks login and API access.
   */
  suspendUser(id: string): User {
    const user = this.userRepo.findById(id);
    if (!user) {
      throw new Error("User not found");
    }
    user.suspend();
    this.userRepo.save(user);
    return user;
  }

  /**
   * Reactivate a suspended user.
   */
  reactivateUser(id: string): User {
    const user = this.userRepo.findById(id);
    if (!user) {
      throw new Error("User not found");
    }
    user.reactivate();
    this.userRepo.save(user);
    return user;
  }

  /**
   * Delete a user (soft delete — marks as deleted, retains record).
   */
  deleteUser(id: string): User {
    const user = this.userRepo.findById(id);
    if (!user) {
      throw new Error("User not found");
    }
    user.delete();
    this.userRepo.save(user);
    return user;
  }
}
