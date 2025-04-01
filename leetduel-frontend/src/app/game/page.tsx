"use client";
import { useState, useRef, useEffect, Suspense } from "react";
import { useGame } from "../../context/GameContext";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Problem,
  MessageData,
  GameData,
  TimeData,
  PlayerData,
} from "../../types";
import socket from "../../socket";
import Editor from "@monaco-editor/react";
import parse from "html-react-parser";
import Button from "../button";
import color from "../colors";

const getDifficultyColor = (difficulty: string) => {
  switch (difficulty.toLowerCase()) {
    case "easy":
      return "text-green-500";
    case "medium":
      return "text-orange-400";
    case "hard":
      return "text-red-500";
    default:
      return "";
  }
};

const starterCode = (problem: Problem) =>
  problem
    ? problem.function_signature +
      `:` +
      `
    # your code here
    return`
    : ``;

function GameContent() {
  const [consoleOutput, setConsoleOutput] = useState("Test case output");
  const [chatMessages, setChatMessages] = useState<MessageData[]>([
    { message: "Game started!", bold: true, color: "" },
  ]);
  const [chatInput, setChatInput] = useState("");

  const editorRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const editorContainerRef = useRef<HTMLDivElement>(null);

  const { problem, username, setProblem } = useGame();
  const router = useRouter();
  const searchParams = useSearchParams();
  const party = searchParams.get("party") || "Unknown";
  const initialTime = 0;
  const [timeLeft, setTimeLeft] = useState(initialTime);
  const [buttonDisabled, setButtonDisabled] = useState(false);
  const [skipButtonDisabled, setSkipButtonDisabled] = useState(false);
  const [passedAll, setPassedAll] = useState(false);

  const [code, setCode] = useState(starterCode(problem));
  const [codeUpdateTimer, setCodeUpdateTimer] = useState<NodeJS.Timeout | null>(
    null
  );
  const lastCodeRef = useRef(code);
  const scrollIfAppendedRef = useRef(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const keyCounterRef = useRef(0);

  const [showMembers, setShowMembers] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const [members, setMembers] = useState<string[]>([]);
  const [screen, setScreen] = useState<string>(username);

  const [homeCode, setHomeCode] = useState(starterCode(problem));
  const [homeConsole, setHomeConsole] = useState("Test case output");

  const [runLoading, setRunLoading] = useState(false);
  const [leaveLoading, setLeaveLoading] = useState(false);
  const [skipLoading, setSkipLoading] = useState(false);
  const [playersLoading, setPlayersLoading] = useState(false);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        showMembers &&
        modalRef.current &&
        !modalRef.current.contains(event.target as Node)
      ) {
        setShowMembers(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showMembers]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      setIsDarkMode(mediaQuery.matches);
      const handler = (e: MediaQueryListEvent) => setIsDarkMode(e.matches);
      mediaQuery.addEventListener("change", handler);
      return () => mediaQuery.removeEventListener("change", handler);
    }
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  useEffect(() => {
    if (!problem) {
      router.push("/");
    }
    socket.on("code_submitted", (data: MessageData) => {
      setConsoleOutput(data.message);
      setHomeConsole(data.message);
      socket.emit("console_update", {
        party_code: party,
        console_output: data.message,
      });
      setButtonDisabled(false);
    });

    socket.on("message_received", (data: MessageData) => {
      setChatMessages((prevMessages) => [
        ...prevMessages,
        {
          message: `${data.username}: ${data.message}`,
          bold: false,
          color: "",
        },
      ]);
    });

    socket.on("player_submit", (data: MessageData) => {
      setChatMessages((prevMessages) => [...prevMessages, data]);
    });

    socket.on("announcement", (data: MessageData) => {
      setChatMessages((prevMessages) => [
        ...prevMessages,
        { message: data.message, bold: true, color: "" },
      ]);
    });

    socket.on("game_over", () => {
      router.push(
        `/?party=${encodeURIComponent(party)}&username=${encodeURIComponent(
          username
        )}`
      );
    });

    socket.on("leave_party", () => {
      router.push(`/`);
    });

    socket.on("game_started", (data: GameData) => {
      setSkipButtonDisabled(false);
      setProblem(data.problem);
      setScreen(username);
      setCode(starterCode(data.problem));
      setConsoleOutput("Test case output");
      setHomeCode(starterCode(data.problem));
      setHomeConsole("Test case output");
      setPassedAll(false);
      retrieveTime();
      socket.emit("code_update", { party_code: party, code: code });
      socket.emit("console_update", {
        party_code: party,
        console_output: consoleOutput,
      });
      router.push(`/game?party=${encodeURIComponent(data.party_code)}`);
    });

    socket.on("update_time", (data: TimeData) => {
      setTimeLeft(Math.round(data.time_left));
    });

    socket.on("passed_all", () => {
      setPassedAll(true);
    });

    socket.on("send_players", (data: PlayerData) => {
      setMembers(data.players ? data.players : []);
    });

    socket.on("updated_code", (data: MessageData) => {
      setCode(data.message);
    });

    socket.on("updated_console", (data: MessageData) => {
      setConsoleOutput(data.message);
    });

    return () => {
      socket.off("code_submitted");
      socket.off("message_received");
      socket.off("player_submit");
      socket.off("announcement");
      socket.off("game_over");
      socket.off("leave_party");
      socket.off("game_started");
      socket.off("update_time");
      socket.off("passed_all");
      socket.off("send_players");
      socket.off("updated_code");
      socket.off("updated_console");
    };
  }, [problem, router]);

  useEffect(() => {
    if (
      editorContainerRef.current &&
      editorRef.current &&
      lineNumbersRef.current
    ) {
      editorRef.current.style.height = "auto";
      const newHeight = editorRef.current.scrollHeight;
      editorRef.current.style.height = newHeight + "px";
      lineNumbersRef.current.style.height = newHeight + "px";
      if (
        code.startsWith(lastCodeRef.current) &&
        code.length > lastCodeRef.current.length &&
        scrollIfAppendedRef.current
      ) {
        editorContainerRef.current.scrollTop =
          editorContainerRef.current.scrollHeight;
      }
      lastCodeRef.current = code;
      scrollIfAppendedRef.current = false;
    }
  }, [code]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  function retrieveTime() {
    socket.emit("retrieve_time", {
      party_code: party,
    });
  }

  useEffect(() => {
    retrieveTime();
  }, []);

  const runCode = () => {
    setConsoleOutput("Running code...");
    setButtonDisabled(true);
    socket.emit("submit_code", {
      code: code,
      party_code: party,
      username: username,
    });
  };

  const sendMessage = () => {
    if (chatInput.trim()) {
      socket.emit("chat_message", {
        message: chatInput,
        party_code: party,
        username: username,
      });
      setChatInput("");
    }
  };

  const leaveGame = () => {
    socket.emit("leave_party", { party_code: party, username });
    router.push(`/`);
  };

  const skipProblem = () => {
    setSkipButtonDisabled(true);
    socket.emit("skip_problem", { party_code: party });
    console.log("Skip problem clicked");
  };

  const handleCodeChange = (e: string | undefined) => {
    if (screen !== username) {
      return;
    }
    const newCode = e || "";
    setCode(newCode);
    setHomeCode(newCode);
    keyCounterRef.current++;
    if (codeUpdateTimer) {
      clearTimeout(codeUpdateTimer);
    }
    if (keyCounterRef.current >= 4) {
      updateCode(newCode);
      return;
    }
    setCodeUpdateTimer(
      setTimeout(() => {
        updateCode(newCode);
      }, 1000)
    );
  };

  const updateCode = (updatedCode: string) => {
    socket.emit("code_update", { party_code: party, code: updatedCode });
    keyCounterRef.current = 0;
  };

  const handlePlayersClick = () => {
    console.log("players key pressed");
    socket.emit("retrieve_players", { party_code: party });
    setShowMembers((prev) => !prev);
  };

  const handleSpectateClick = (member: string) => {
    setShowMembers(false);
    if (member === username) {
      setScreen(username);
      setCode(homeCode);
      setConsoleOutput(homeConsole);
      setButtonDisabled(false);
      socket.emit("leave_spectate_rooms", {
        party_code: party,
      });
      return;
    }
    setScreen(member);
    socket.emit("retrieve_code", { party_code: party, username: member });
  };

  return (
    <>
      <div className="fixed top-4 right-[18%] z-50">
        <button
          onClick={handlePlayersClick}
          className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md shadow"
        >
          Players
        </button>
      </div>
      {showMembers && (
        <div className="absolute top-15 right-[18%] z-50" ref={modalRef}>
          <div className="bg-white dark:bg-gray-700 p-6 rounded shadow-lg w-80">
            <ul>
              {members.map((member, index) => (
                <li
                  key={index}
                  className="flex justify-between items-center py-2 border-b border-gray-300 dark:border-gray-400"
                >
                  <span>{member}</span>
                  <button
                    className={`px-2 py-1 rounded text-white ${
                      member === username
                        ? "bg-green-600 hover:bg-green-700"
                        : passedAll
                        ? "bg-green-600 hover:bg-green-700"
                        : "bg-gray-500 cursor-not-allowed"
                    }`}
                    disabled={member === username ? false : !passedAll}
                    onClick={() => handleSpectateClick(member)}
                  >
                    {member === username ? "Home" : "Spectate"}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      <div
        className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6 pr-[18%] text-gray-900 dark:text-gray-100"
        style={{ position: "relative" }}
      >
        <div className="absolute top-0 left-0 m-4 p-2 bg-white dark:bg-gray-800 rounded shadow text-lg">
          {formatTime(timeLeft)}
        </div>
        <div className="w-full h-[75vh] mx-auto mr-[16.66%]">
          <h1 className="text-4xl mb-8 text-center">Leetduel</h1>
          <div className="flex flex-col md:flex-row h-full gap-2 w-full">
            <div className="relative md:w-1/2 bg-white dark:bg-gray-800 shadow rounded-lg p-6 border-1 border-gray-500">
              <h2 className="text-2xl font-semibold mb-4">{problem?.name}</h2>
              <h2 className="text-l font-semibold mb-4">
                <span
                  className={`px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 ${
                    problem?.difficulty
                      ? getDifficultyColor(problem.difficulty)
                      : ""
                  }`}
                >
                  {problem?.difficulty}
                </span>
              </h2>
              {problem ? (
                <div className="overflow-y-auto max-h-[80%] text-sm leading-relaxed whitespace-normal">
                  {parse(problem.description)}
                </div>
              ) : (
                "Loading problem description..."
              )}
              <button
                onClick={runCode}
                disabled={screen !== username || buttonDisabled}
                className={`absolute bottom-4 right-4 ${
                  screen !== username || buttonDisabled
                    ? "bg-gray-500 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700"
                } text-white py-2 px-4 rounded-lg transition`}
              >
                Run Code
              </button>
            </div>
            <div className="md:w-1/2 flex flex-col">
              <div className="relative flex h-[55vh] bg-white dark:bg-[#1E1E1E] rounded-lg border border-gray-300 dark:border-gray-600 py-2">
                <Editor
                  height="100%"
                  defaultLanguage="python"
                  value={code}
                  onChange={handleCodeChange}
                  theme={isDarkMode ? "vs-dark" : "light"}
                  options={{
                    fontSize: 15,
                    padding: { top: 16, bottom: 16 },
                    minimap: { enabled: false },
                    inlineSuggest: { enabled: false },
                    folding: false,
                    readOnly: screen !== username,
                  }}
                />
              </div>
              <div
                className="mt-2 bg-white dark:bg-black text-black dark:text-green-400 font-mono p-4 rounded-lg h-[20vh] overflow-auto"
                style={{ whiteSpace: "pre-wrap" }}
              >
                {consoleOutput}
              </div>
            </div>
          </div>
          <div className="fixed top-0 right-0 h-screen w-1/6">
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 h-full flex flex-col">
              <h2 className="text-xl mb-4">Party Chat</h2>
              <div
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto mb-4 space-y-2"
              >
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`text-sm font-mono ${
                      msg.bold ? "font-bold" : ""
                    } ${!msg.color ? "text-gray-900 dark:text-gray-100" : ""}`}
                    style={msg.color ? { color: msg.color } : {}}
                  >
                    {msg.message}
                  </div>
                ))}
              </div>
              <div className="flex">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      sendMessage();
                    }
                  }}
                  placeholder="Type your message..."
                  className="flex-1 min-w-0 px-3 py-2 rounded-l-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                />
                <button
                  onClick={sendMessage}
                  className="flex-shrink-0 bg-blue-600 hover:bg-blue-700 text-white px-4 rounded-r-lg transition"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
        <div className="fixed bottom-0 left-0 m-4 flex gap-2">
          <button
            onClick={leaveGame}
            className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded"
          >
            Leave Game
          </button>
          <button
            onClick={skipProblem}
            disabled={skipButtonDisabled}
            className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded"
          >
            Skip Problem
          </button>
        </div>
        <div className="fixed bottom-4 right-[18%] z-50">
          {/* <button className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded">
            Help
          </button> */}
        </div>
      </div>
    </>
  );
}

export default function GamePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <GameContent />
    </Suspense>
  );
}
