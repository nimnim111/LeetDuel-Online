"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";

interface LadderEntry {
  rank: number;
  username: string;
  total_score: number;
}

const BACKEND_URL = "https://leetduel-online.onrender.com/";

export default function LadderPage() {
  const router = useRouter();
  const [ladderData, setLadderData] = useState<LadderEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Floating light effect state
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
    const fetchLadderData = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/ladder`);
        if (!response.ok) {
          throw new Error(`Failed to load leaderboard. Please try again later.`);
        }
        const data = await response.json();
        // Map to only include the fields we want
        setLadderData(data.entries.map((entry: any) => ({
          rank: entry.rank,
          username: entry.username,
          total_score: entry.total_score
        })));
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load leaderboard");
        setLoading(false);
      }
    };
    fetchLadderData();
  }, [retryCount]);

  const handleRetry = () => {
    setError(null);
    setLoading(true);
    setRetryCount(prev => prev + 1);
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
      <div className="relative z-10 w-full max-w-2xl p-8 bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-300 dark:border-gray-700 flex flex-col items-center leaderboard-outer text-gray-900 dark:text-white font-inter">
        <h1 className="text-3xl font-normal mb-6 text-center">Leaderboard</h1>
        {error ? (
          <div className="w-full text-center">
            <h2 className="text-xl font-bold text-red-400 mb-2">Error</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
            <div className="space-x-4">
              <button
                onClick={handleRetry}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                Retry
              </button>
              <button
                onClick={() => router.push("/")}
                className="inline-flex items-center px-4 py-2 border border-gray-500 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Back to Home
              </button>
            </div>
          </div>
        ) : loading ? (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading leaderboard...</p>
          </div>
        ) : (
          <div className="w-full overflow-x-auto">
            <table className="min-w-full text-sm text-left text-gray-900 dark:text-white">
              <thead className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                <tr>
                  <th className="px-4 py-2 rounded-tl-lg">Rank</th>
                  <th className="px-4 py-2">Username</th>
                  <th className="px-4 py-2 rounded-tr-lg">Score</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
                {ladderData.map((entry) => (
                  <tr key={entry.username}>
                    <td className="px-4 py-2 font-medium">#{entry.rank}</td>
                    <td className="px-4 py-2">{entry.username}</td>
                    <td className="px-4 py-2">{entry.total_score.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              onClick={() => router.push("/")}
              className="mt-8 w-full border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 py-2 rounded-md transition home-btn"
            >
              Back to Home
            </button>
          </div>
        )}
      </div>
    </div>
  );
} 
