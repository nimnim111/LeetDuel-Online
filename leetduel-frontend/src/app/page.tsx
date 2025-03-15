"use client";
import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import socket from "../socket";
import { useGame } from "../context/GameContext";

enum PartyStatus {
  UNJOINED = "unjoined",
  JOINED = "joined",
  CREATED = "created",
}

// New inner component that uses useSearchParams
function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setProblem, setPartyCode, setUsername } = useGame();
  const [username, localSetUsername] = useState("");
  const [message, setMessage] = useState("");
  const [members, setMembers] = useState<string[]>([]);
  const [partyStatus, setPartyStatus] = useState<PartyStatus>(
    PartyStatus.UNJOINED
  );
  const [localPartyCode, setLocalPartyCode] = useState("");
  const [timeLimit, setTimeLimit] = useState("");
  const [easy, setEasy] = useState(true);
  const [medium, setMedium] = useState(true);
  const [hard, setHard] = useState(true);
  const [showBanner, setShowBanner] = useState(false);
  const [goodBanner, setGoodBanner] = useState(true);

  useEffect(() => {
    const qpParty = searchParams.get("party");
    const qpUsername = searchParams.get("username");
    if (qpParty) {
      setLocalPartyCode(qpParty);
      setPartyCode(qpParty);
      setPartyStatus(PartyStatus.JOINED);
      if (qpUsername) {
        localSetUsername(qpUsername);
      }
      setMembers(qpUsername ? [qpUsername] : []);
    }
  }, [searchParams, setPartyCode]);

  useEffect(() => {
    socket.on("party_created", (data) => {
      setGoodBanner(true);
      setMessage(`Party created with code: ${data.party_code}`);
      setLocalPartyCode(data.party_code);
      setPartyCode(data.party_code);
      setPartyStatus(PartyStatus.CREATED);
      setUsername(username);
      setMembers(data.members ? data.members : [data.username]);
    });
    socket.on("player_joined", (data) => {
      setGoodBanner(true);
      setMessage(`${message}\n${data.username} joined`);
      if (partyStatus !== PartyStatus.CREATED) {
        setPartyStatus(PartyStatus.JOINED);
      }
      setUsername(username);
      setMembers(data.players);
    });
    socket.on("player_left", (data) => {
      setMembers((prev) => prev.filter((member) => member !== data.username));
    });
    socket.on("game_started", (data) => {
      console.log(data);
      setGoodBanner(true);
      setMessage(`Loading game...`);
      setProblem(data.problem);
      setPartyCode(data.party_code);
      router.push(
        `/game?party=${encodeURIComponent(
          data.party_code
        )}&timeLimit=${encodeURIComponent(data.time_limit)}`
      );
    });
    socket.on("error", (data) => {
      setGoodBanner(false);
      setMessage(`Error: ${data.message}`);
    });
    return () => {
      socket.off("party_created");
      socket.off("player_joined");
      socket.off("player_left");
      socket.off("game_started");
      socket.off("error");
    };
  }, [router, setProblem, setPartyCode, setUsername, username, message]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (message) {
      setShowBanner(true);
      timer = setTimeout(() => setShowBanner(false), 3000);
    }
    return () => clearTimeout(timer);
  }, [message]);

  useEffect(() => {
    if (partyStatus) {
      console.log("Party status: ", partyStatus);
    }
  }, [partyStatus, setPartyStatus]);

  const createParty = () => {
    if (username) {
      socket.emit("create_party", { username });
      setPartyStatus(PartyStatus.CREATED);
    }
  };

  const joinParty = () => {
    if (username && localPartyCode) {
      socket.emit("join_party", { username, party_code: localPartyCode });
      setPartyStatus(PartyStatus.JOINED);
    }
  };

  const startGame = () => {
    if (isNaN(Number(timeLimit))) {
      setGoodBanner(false);
      setMessage("Time limit must be a number.");
      return;
    }
    if (timeLimit && Number(timeLimit) < 1) {
      setGoodBanner(false);
      setMessage("Time limit must be at least 1 minute.");
      return;
    }
    if (!easy && !medium && !hard) {
      setGoodBanner(false);
      setMessage("Please select at least one difficulty level.");
      return;
    }
    if (localPartyCode) {
      socket.emit("start_game", {
        party_code: localPartyCode,
        time_limit: timeLimit,
        easy,
        medium,
        hard,
      });
    }
  };

  const leaveGame = () => {
    socket.emit("leave_party", { party_code: localPartyCode, username });
    localSetUsername("");
    setLocalPartyCode("");
    setPartyStatus(PartyStatus.UNJOINED);
    setPartyCode("");
    setUsername("");
    setMessage("");
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-100 dark:bg-gray-900 transition-colors relative">
      {showBanner && message && (
        <div className="absolute top-0 left-0 w-full flex justify-center p-4 transition-all">
          <div
            className={`${
              goodBanner
                ? "bg-blue-200 text-blue-900"
                : "bg-red-200 text-red-900"
            } p-3 rounded shadow-md relative max-w-xl w-full`}
          >
            <button
              onClick={() => {
                setShowBanner(false);
                setMessage("");
              }}
              className="absolute top-2 right-2 text-blue-900 font-bold hover:text-blue-600 cursor-pointer"
            >
              ✕
            </button>
            <p>{message}</p>
          </div>
        </div>
      )}
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-xl p-8 w-full max-w-md font-inter">
        <h1 className="text-3xl text-gray-900 dark:text-white mb-6 text-center">
          LeetDuel
        </h1>
        <div className="space-y-4 mb-6">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => localSetUsername(e.target.value)}
            disabled={partyStatus !== PartyStatus.UNJOINED}
            className="w-full px-4 py-3 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
          />
          <input
            type="text"
            placeholder="Party Code"
            value={localPartyCode}
            onChange={(e) => setLocalPartyCode(e.target.value)}
            disabled={partyStatus !== PartyStatus.UNJOINED}
            className="w-full px-4 py-3 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
          />
        </div>
        {partyStatus === PartyStatus.UNJOINED && (
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
        {partyStatus !== PartyStatus.UNJOINED && (
          <div className="transition-all duration-500 transform translate-y-0 opacity-100 mb-6">
            <div className="mt-4 flex items-center space-x-6">
              <label className="flex items-center space-x-1">
                <input
                  type="checkbox"
                  className="form-checkbox text-blue-600"
                  checked={easy}
                  onChange={(e) => setEasy(e.target.checked)}
                  disabled={partyStatus !== PartyStatus.CREATED}
                />
                <span className="text-gray-800 dark:text-gray-200">Easy</span>
              </label>
              <label className="flex items-center space-x-1">
                <input
                  type="checkbox"
                  className="form-checkbox text-green-600"
                  checked={medium}
                  onChange={(e) => setMedium(e.target.checked)}
                  disabled={partyStatus !== PartyStatus.CREATED}
                />
                <span className="text-gray-800 dark:text-gray-200">Medium</span>
              </label>
              <label className="flex items-center space-x-1">
                <input
                  type="checkbox"
                  className="form-checkbox text-red-600"
                  checked={hard}
                  onChange={(e) => setHard(e.target.checked)}
                  disabled={partyStatus !== PartyStatus.CREATED}
                />
                <span className="text-gray-800 dark:text-gray-200">Hard</span>
              </label>
            </div>
            <div className="mt-4">
              <input
                type="number"
                placeholder="Time limit (minutes)"
                value={timeLimit}
                onChange={(e) => setTimeLimit(e.target.value)}
                disabled={partyStatus !== PartyStatus.CREATED}
                className="w-full px-4 py-3 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition mb-3"
              />
            </div>
            <button
              onClick={startGame}
              className="w-full bg-purple-600 dark:bg-purple-500 text-white py-3 rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 transition mb-3"
            >
              Start Game
            </button>
            <button
              onClick={leaveGame}
              className="w-full bg-red-600 dark:bg-red-500 text-white py-3 rounded-lg hover:bg-red-700 dark:hover:bg-red-600 transition"
            >
              Leave Game
            </button>
            <div className="mt-4">
              <h2 className="text-xl font-bold mb-2">Members</h2>
              <ul className="list-inside">
                {members.map((member, idx) => (
                  <li key={idx} className="text-lg">
                    {member}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
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
