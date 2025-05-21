import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics, isSupported } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyDmgrLZNes7VmGjRA3hCcXDTvbsq0OgK9Y",
  authDomain: "leetduel2.firebaseapp.com",
  projectId: "leetduel2",
  storageBucket: "leetduel2.firebasestorage.app",
  messagingSenderId: "1033323686755",
  appId: "1:1033323686755:web:492bb19f05c2796b158156",
  measurementId: "G-89JPNDQM7P"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

// Initialize analytics only on the client side
let analytics = null;
if (typeof window !== 'undefined') {
  isSupported().then(yes => yes && (analytics = getAnalytics(app)));
} 