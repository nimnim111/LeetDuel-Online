"use client";
import React, { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import socket from "../socket";
import { useGame } from "@/context/GameContext";
import { PlayerData, GameData, ErrorData } from "../types";
import Button from "./button";
import Color from "./colors";
import { initializeApp } from "firebase/app";
import { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, User } from "firebase/auth";
import { getAnalytics, isSupported } from "firebase/analytics";

// Firebase configuration
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
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// Initialize analytics only on the client side
let analytics = null;
if (typeof window !== 'undefined') {
  isSupported().then(yes => yes && (analytics = getAnalytics(app)));
}

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setProblem, setPartyCode, setUsername } = useGame();
  const [user, setUser] = useState<User | null>(null);
  const [message, setMessage] = useState("");
  const [members, setMembers] = useState<string[]>([]);
  const [matchmakingLoading, setMatchmakingLoading] = useState(false);
  const [showBanner, setShowBanner] = useState(false);
  const [goodBanner, setGoodBanner] = useState(true);

  const [delayedMousePos, setDelayedMousePos] = useState({ x: 0, y: 0 });
  const mousePosRef = useRef({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    mousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  useEffect(() => {
    let animationFrameId: number;
    const updateDelayedPos = () => {
      setDelayedMousePos((prev) => ({
        x: prev.x + (mousePosRef.current.x - prev.x) * 0.05,
        y: prev.y + (mousePosRef.current.y - prev.y) * 0.05,
      }));
      animationFrameId = requestAnimationFrame(updateDelayedPos);
    };
    animationFrameId = requestAnimationFrame(updateDelayedPos);
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  useEffect(() => {
    // Listen for auth state changes
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    socket.on("game_started", (data: GameData) => {
      setGoodBanner(true);
      setProblem(data.problem);
      setPartyCode(data.party_code);
      router.push(`/game?party=${encodeURIComponent(data.party_code)}`);
    });
    socket.on("error", (data: ErrorData) => {
      setMatchmakingLoading(false);
      setGoodBanner(false);
      setMessage(`Error: ${data.message}`);
    });
    return () => {
      socket.off("game_started");
      socket.off("error");
    };
  }, [router, setProblem, setPartyCode]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (message) {
      setShowBanner(true);
      timer = setTimeout(() => setShowBanner(false), 3000);
    }
    return () => clearTimeout(timer);
  }, [message]);

  const handleGoogleSignIn = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      setUser(result.user);
    } catch (error) {
      console.error("Error signing in with Google:", error);
      setGoodBanner(false);
      setMessage("Error signing in with Google");
    }
  };

  const handleSignOut = async () => {
    try {
      await auth.signOut();
      setUser(null);
    } catch (error) {
      console.error("Error signing out:", error);
      setGoodBanner(false);
      setMessage("Error signing out");
    }
  };

  const startMatchmaking = () => {
    if (!user) {
      setGoodBanner(false);
      setMessage("Please sign in to start matchmaking");
      return;
    }
    setMatchmakingLoading(true);
    socket.emit("start_matchmaking", {
      username: user.displayName,
      email: user.email,
      uid: user.uid,
      time_limit: 15, // Default 15 minutes
      rounds: 1,
      easy: true,
      medium: true,
      hard: true,
    });
  };

  return (
    <div
      className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center"
      onMouseMove={handleMouseMove}
    >
      <div className="fixed inset-0 pointer-events-none">
        <div
          className="absolute w-96 h-96 rounded-full bg-blue-200 dark:bg-blue-900 opacity-20 blur-3xl"
          style={{
            left: `${delayedMousePos.x - 192}px`,
            top: `${delayedMousePos.y - 192}px`,
            transition: "transform 0.1s ease-out",
          }}
        />
      </div>
      <div className="relative z-10 w-full max-w-4xl mx-auto px-4">
        {showBanner && (
          <div
            className={`fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg shadow-lg transition-all duration-500 ${
              goodBanner
                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100"
                : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100"
            }`}
          >
            {message}
          </div>
        )}
        <div className="flex justify-center">
          <div className="bg-white dark:bg-gray-900 border-1 border-black dark:border-gray-300 transition duration-500 hover:border-green-400 shadow-lg rounded-xl p-8 w-full max-w-md font-inter">
            <h1 className="text-3xl text-gray-900 dark:text-white mb-6 text-center">
              LeetDuel Online
            </h1>
            {!user ? (
              <div className="space-y-4 mb-6">
                <Button
                  handleClick={handleGoogleSignIn}
                  color={Color("blue")}
                  loading={false}
                  setLoading={() => {}}
                >
                  Sign in with Google
                </Button>
              </div>
            ) : (
              <div className="space-y-4 mb-6">
                <div className="flex items-center space-x-4 mb-4">
                  {user.photoURL && (
                    <img
                      src={user.photoURL}
                      alt="Profile"
                      className="w-10 h-10 rounded-full"
                    />
                  )}
                  <div>
                    <p className="text-gray-900 dark:text-white font-medium">
                      {user.displayName}
                    </p>
                    <p className="text-gray-600 dark:text-gray-400 text-sm">
                      {user.email}
                    </p>
                  </div>
                </div>
                <Button
                  loading={matchmakingLoading}
                  setLoading={setMatchmakingLoading}
                  handleClick={startMatchmaking}
                  color={Color("blue")}
                >
                  Find Match
                </Button>
                <Button
                  handleClick={handleSignOut}
                  color={Color("red")}
                  loading={false}
                  setLoading={() => {}}
                >
                  Sign Out
                </Button>
                <a
                  href="/ladder"
                  className="block w-full text-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                >
                  View Leaderboard
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HomeContent />
    </Suspense>
  );
}
