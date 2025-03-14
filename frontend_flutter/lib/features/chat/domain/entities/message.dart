class Message {
  final String text;
  final bool isUser;
  final DateTime timestamp;

  Message({
    required this.text,
    required this.isUser,
    required this.timestamp,
  });

  // JSON 변환 메서드 추가
  Map<String, dynamic> toJson() {
    return {
      'text': text,
      'isUser': isUser,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  // JSON에서 객체 생성 메서드 추가
  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      text: json['text'] as String,
      isUser: json['isUser'] as bool,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}
