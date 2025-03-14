enum Emotion {
  veryBad, // 매우 부정적
  bad, // 부정적
  neutral, // 보통
  good, // 긍정적
  veryGood, // 매우 긍정적
}

extension EmotionExtension on Emotion {
  String get emoji {
    switch (this) {
      case Emotion.veryBad:
        return '😡';
      case Emotion.bad:
        return '😢';
      case Emotion.neutral:
        return '😐';
      case Emotion.good:
        return '🙂';
      case Emotion.veryGood:
        return '😄';
    }
  }

  String get description {
    switch (this) {
      case Emotion.veryBad:
        return '매우 부정적\n(분노, 좌절)';
      case Emotion.bad:
        return '부정적\n(불안, 피로)';
      case Emotion.neutral:
        return '보통\n(무난, 평범)';
      case Emotion.good:
        return '긍정적\n(만족, 기쁨)';
      case Emotion.veryGood:
        return '매우 긍정적\n(성취, 행복)';
    }
  }
}
