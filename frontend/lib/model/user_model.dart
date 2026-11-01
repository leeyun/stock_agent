class UserModel {
  final int id;
  final String username;
  final String email;
  final String? createdAt;

  UserModel({
    required this.id,
    required this.username,
    required this.email,
    this.createdAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] ?? 0,
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      createdAt: json['created_at'],
    );
  }
}