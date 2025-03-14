import 'package:hive/hive.dart';
import 'emotion.dart';

class EmotionAdapter extends TypeAdapter<Emotion> {
  @override
  final int typeId = 1;

  @override
  Emotion read(BinaryReader reader) {
    return Emotion.values[reader.readInt()];
  }

  @override
  void write(BinaryWriter writer, Emotion obj) {
    writer.writeInt(obj.index);
  }
}
