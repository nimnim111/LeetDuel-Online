"use client";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import socket from "../socket";
import { useGame } from "../context/GameContext";

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setProblem, setPartyCode, setUsername } = useGame();
  const [username, localSetUsername] = useState("");
  const [message, setMessage] = useState("");
  const [joined, setJoined] = useState(false);
  const [localPartyCode, setLocalPartyCode] = useState("");

  // Check for party in query parameters so that joined remains true
  useEffect(() => {
    const qpParty = searchParams.get("party");
    const qpUsername = searchParams.get("username");
    if (qpParty) {
      setLocalPartyCode(qpParty);
      setPartyCode(qpParty);
      setJoined(true);
      if (qpUsername) {
        localSetUsername(qpUsername);
      }
    }
  }, [searchParams, setPartyCode]);

  useEffect(() => {
    socket.on("party_created", (data) => {
      setMessage(
        `Party created with code: ${data.party_code}\nMembers:\n${data.username}`
      );
      setLocalPartyCode(data.party_code);
      setPartyCode(data.party_code);
      setJoined(true);
      setUsername(username);
    });
    socket.on("player_joined", (data) => {
      setMessage(`${message + "\n" + username}`);
      setJoined(true);
      setUsername(username);
    });
    socket.on("game_started", (data) => {
      console.log(data);
      setMessage(`Game started! Problem: ${data.problem.title}`);
      setProblem(data.problem);
      setPartyCode(data.party_code);
      router.push(`/game?party=${encodeURIComponent(data.party_code)}`);
    });
    socket.on("error", (data) => {
      setMessage(`Error: ${data.message}`);
    });
    return () => {
      socket.off("party_created");
      socket.off("player_joined");
      socket.off("game_started");
      socket.off("error");
    };
  }, [router, setProblem, setPartyCode, setUsername, username, message]);

  const createParty = () => {
    if (username) {
      socket.emit("create_party", { username });
    }
  };

  const joinParty = () => {
    if (username && localPartyCode) {
      socket.emit("join_party", { username, party_code: localPartyCode });
    }
  };

  const startGame = () => {
    if (localPartyCode) {
      socket.emit("start_game", { party_code: localPartyCode });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-100 dark:bg-gray-900 transition-colors">
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-xl p-8 w-full max-w-md font-inter">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 text-center">
          LeetDuel
        </h1>
        <div className="space-y-4 mb-6">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => localSetUsername(e.target.value)}
            disabled={joined}
            className="w-full px-4 py-3 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
          />
          <input
            type="text"
            placeholder="Party Code"
            value={localPartyCode}
            onChange={(e) => setLocalPartyCode(e.target.value)}
            disabled={joined}
            className="w-full px-4 py-3 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
          />
        </div>
        {!joined && (
          <div className="flex flex-col space-y-3 mb-6">
            <button
              onClick={createParty}
              className="w-full bg-blue-600 dark:bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition"
            >
              Create Party
            </button>
            <button
              onClick={joinParty}
              className="w-full bg-green-600 dark:bg-green-500 text-white py-3 rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition"
            >
              Join Party
            </button>
          </div>
        )}
        {joined && (
          <div className="transition-all duration-500 transform translate-y-0 opacity-100 mb-6">
            <button
              onClick={startGame}
              className="w-full bg-purple-600 dark:bg-purple-500 text-white py-3 rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 transition"
            >
              Start Game
            </button>
          </div>
        )}
        {message && (
          <p className="text-center text-lg text-gray-800 dark:text-gray-200">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
