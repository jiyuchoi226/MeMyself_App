import 'package:flutter/material.dart';

class FadePageRoute<T> extends PageRoute<T> {
  final Widget child;

  FadePageRoute({required this.child});

  @override
  Color? get barrierColor => null;

  @override
  String? get barrierLabel => null;

  @override
  bool get maintainState => true;

  @override
  Duration get transitionDuration => const Duration(milliseconds: 300);

  @override
  Widget buildPage(context, animation, secondaryAnimation) {
    return FadeTransition(
      opacity: animation,
      child: child,
    );
  }
}
