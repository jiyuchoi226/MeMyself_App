
abstract class Failure {
  const Failure();
}

class ServerFailure extends Failure {}

class CacheFailure extends Failure {
  const CacheFailure();
}
