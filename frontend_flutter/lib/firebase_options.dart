import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    return android;
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyDUEwmZoG_-cJ-X-IZAF--VPHUUvD_ZqHk',
    appId: '1:516077214206:android:d4a949c7f05fa8eb4c88af',
    messagingSenderId: '516077214206',
    projectId: 'memyself-451510',
    storageBucket: 'memyself-451510.firebasestorage.app',
  );
}
