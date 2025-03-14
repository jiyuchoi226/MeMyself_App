import 'package:google_sign_in/google_sign_in.dart';
import '../models/calendar_event.dart';
import '../services/calendar_api_service.dart';

class GoogleCalendarRepository {
  final CalendarApiService _apiService;
  final GoogleSignIn _googleSignIn;

  GoogleCalendarRepository(this._apiService, this._googleSignIn);

  Future<String?> _refreshAccessToken() async {
    try {
      final googleUser = await _googleSignIn.signInSilently();
      if (googleUser == null) {
        throw Exception('Failed to refresh token: User not signed in');
      }

      final googleAuth = await googleUser.authentication;
      return googleAuth.accessToken;
    } catch (e) {
      print('Error refreshing access token: $e');
      return null;
    }
  }

  Future<List<CalendarEvent>> getEvents(DateTime start, DateTime end) async {
    try {
      var events = await _apiService.fetchEvents(start, end);
      return events;
    } catch (e) {
      if (e.toString().contains('invalid_token')) {
        final newToken = await _refreshAccessToken();
        if (newToken != null) {
          return await _apiService.fetchEvents(start, end);
        }
      }
      rethrow;
    }
  }
}
