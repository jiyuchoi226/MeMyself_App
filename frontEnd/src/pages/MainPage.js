import React from 'react';
import { auth } from '../firebase';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { useAuthState } from 'react-firebase-hooks/auth';
import './MainPage.css';

function MainPage() {
  const [user] = useAuthState(auth);

  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error('Error during sign in:', error);
    }
  };

  const signOut = () => {
    auth.signOut();
  };

  return (
    <div className="main-container">
      <div className="logo-container">
        <img src="/doday-logo.png" alt="Doday Logo" className="logo" />
      </div>
      
      {!user ? (
        <button className="google-login-btn" onClick={signInWithGoogle}>
          Google로 로그인
        </button>
      ) : (
        <div className="user-info">
          <p>환영합니다, {user.displayName}님!</p>
          <button className="logout-btn" onClick={signOut}>
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
}

export default MainPage; 