import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  // Firebase 콘솔에서 가져온 설정을 여기에 넣으세요
  apiKey: "516077214206",
  //authDomain: "your-auth-domain",
  projectId: "memyself-451510",
  storageBucket: "memyself-451510.firebasestorage.app",
  messagingSenderId: "516077214206",
  appId: "1:516077214206:android:d4a949c7f05fa8eb4c88af"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app); 