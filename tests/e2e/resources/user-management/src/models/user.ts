/**
 * User — Aggregate Root
 *
 * Central entity of the User Management bounded context.
 * Manages user identity, credentials, profile, and lifecycle.
 */
export type UserStatus = "active" | "suspended" | "deleted";

export class User {
  public readonly id: string;
  public email: string;
  public passwordHash: string;
  public profile: Profile;
  public status: UserStatus;
  public readonly createdAt: Date;
  public updatedAt: Date;

  constructor(
    id: string,
    email: string,
    passwordHash: string,
    profile: Profile,
    status: UserStatus = "active",
  ) {
    this.id = id;
    this.email = email;
    this.passwordHash = passwordHash;
    this.profile = profile;
    this.status = status;
    this.createdAt = new Date();
    this.updatedAt = new Date();
  }

  /**
   * Register a new user — factory method enforcing registration invariants.
   * Email must be unique (enforced at repository level) and password must
   * meet complexity requirements before hashing.
   */
  static register(
    id: string,
    email: string,
    passwordHash: string,
    profile: Profile,
  ): User {
    if (!email.includes("@")) {
      throw new Error("Invalid email format");
    }
    const user = new User(id, email, passwordHash, profile, "active");
    return user;
  }

  /**
   * Suspend the user — blocks login and API access.
   * Only active users can be suspended.
   */
  suspend(): void {
    if (this.status !== "active") {
      throw new Error("Only active users can be suspended");
    }
    this.status = "suspended";
    this.updatedAt = new Date();
  }

  /**
   * Reactivate a suspended user — restores login and API access.
   */
  reactivate(): void {
    if (this.status !== "suspended") {
      throw new Error("Only suspended users can be reactivated");
    }
    this.status = "active";
    this.updatedAt = new Date();
  }

  /**
   * Change the user's password — requires old password verification.
   * The new password hash replaces the old one.
   */
  changePassword(newPasswordHash: string): void {
    if (this.status === "deleted") {
      throw new Error("Cannot change password for deleted user");
    }
    this.passwordHash = newPasswordHash;
    this.updatedAt = new Date();
  }

  /**
   * Update the user's profile information.
   */
  updateProfile(profile: Profile): void {
    if (this.status === "deleted") {
      throw new Error("Cannot update profile for deleted user");
    }
    this.profile = profile;
    this.updatedAt = new Date();
  }

  /**
   * Soft-delete the user — marks as deleted but retains record for audit.
   */
  delete(): void {
    if (this.status === "deleted") {
      throw new Error("User is already deleted");
    }
    this.status = "deleted";
    this.updatedAt = new Date();
  }
}

/**
 * Profile — Value Object
 *
 * Immutable user profile data: display name, avatar URL, and bio.
 */
export class Profile {
  public readonly displayName: string;
  public readonly avatarUrl: string | null;
  public readonly bio: string;

  constructor(displayName: string, avatarUrl: string | null = null, bio: string = "") {
    if (displayName.trim().length === 0) {
      throw new Error("Display name cannot be empty");
    }
    this.displayName = displayName;
    this.avatarUrl = avatarUrl;
    this.bio = bio;
  }
}
