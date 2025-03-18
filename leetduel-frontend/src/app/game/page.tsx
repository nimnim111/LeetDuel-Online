"use client";
import { useState, useRef, useEffect, Suspense } from "react";
import { useGame, Problem } from "../../context/GameContext";
import { useRouter, useSearchParams } from "next/navigation";
import socket from "../../socket";
import { Fira_Code } from "next/font/google";
import ReactMarkdown from "react-markdown";
import Editor from "@monaco-editor/react";

const firaCode = Fira_Code({
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});

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
  const [chatMessages, setChatMessages] = useState([
    { message: "Game started!", bold: true, color: "white" },
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
  const timeLimitParam = searchParams.get("timeLimit");
  const initialTime = timeLimitParam ? parseInt(timeLimitParam, 10) * 60 : 0;
  const [timeLeft, setTimeLeft] = useState(initialTime);
  const [buttonDisabled, setButtonDisabled] = useState(false);

  const [code, setCode] = useState(starterCode(problem));
  const lastCodeRef = useRef(code);
  const scrollIfAppendedRef = useRef(false);

  useEffect(() => {
    if (initialTime <= 0) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [initialTime]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  useEffect(() => {
    if (!problem) {
      router.push("/");
    }
    socket.on("code_submitted", (data) => {
      setConsoleOutput(data.message);
      setButtonDisabled(false);
    });

    socket.on("message_received", (data) => {
      setChatMessages((prevMessages) => [
        ...prevMessages,
        {
          message: `${data.username}: ${data.message}`,
          bold: false,
          color: "white",
        },
      ]);
    });

    socket.on("player_submit", (data) => {
      setChatMessages((prevMessages) => [...prevMessages, data]);
    });

    socket.on("announcement", (data) => {
      setChatMessages((prevMessages) => [
        ...prevMessages,
        { message: data.message, bold: true, color: "white" },
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

    socket.on("game_started", (data) => {
      setProblem(data.problem);
      setCode(starterCode(data.problem));
      setTimeLeft(initialTime);
      router.push(
        `/game?party=${encodeURIComponent(
          data.party_code
        )}&timeLimit=${encodeURIComponent(data.time_limit)}`
      );
    });

    return () => {
      socket.off("code_submitted");
      socket.off("message_received");
      socket.off("player_submit");
      socket.off("announcement");
      socket.off("game_over");
      socket.off("leave_party");
      socket.off("game_started");
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

  const runCode = () => {
    console.log(party);
    console.log(username);
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
    socket.emit("skip_problem", { party_code: party });
    console.log("Skip problem clicked");
  };

  return (
    <div>
      <div
        className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6 pr-[18%] text-gray-900 dark:text-gray-100"
        style={{ position: "relative" }}
      >
        <div className="absolute top-0 left-0 m-4 p-2 bg-white dark:bg-gray-800 rounded shadow text-lg">
          {formatTime(timeLeft)}
        </div>
        <div className="w-full h-[80vh] mx-auto mr-[16.66%]">
          <h1 className="text-4xl mb-8 text-center">LeetDuel</h1>
          <div className="flex flex-col md:flex-row h-full gap-2 w-full">
            <div className="relative md:w-1/2 bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4">{problem?.name}</h2>
              <h2 className="text-l font-semibold mb-4">
                <span
                  className={`px-2 py-1 rounded bg-gray-700 ${
                    problem?.difficulty
                      ? getDifficultyColor(problem.difficulty)
                      : ""
                  }`}
                >
                  {problem?.difficulty}
                </span>
              </h2>
              {problem ? (
                <div className="overflow-y-auto max-h-[90%] text-sm leading-relaxed">
                  <ReactMarkdown>{problem.description}</ReactMarkdown>
                </div>
              ) : (
                "Loading problem description..."
              )}
              <button
                onClick={runCode}
                disabled={buttonDisabled}
                className="absolute bottom-4 right-4 bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded-lg transition"
              >
                Run Code
              </button>
            </div>
            <div className="md:w-1/2 flex flex-col">
              <div className="relative flex h-[60vh] bg-[#1E1E1E] rounded-lg border border-gray-300 dark:border-gray-600 py-2">
                <Editor
                  height="100%"
                  defaultLanguage="python"
                  value={code}
                  onChange={(e) => setCode(e || "")}
                  theme="vs-dark"
                  options={{
                    fontSize: 15,
                    padding: { top: 16, bottom: 16 },
                    minimap: { enabled: false },
                  }}
                />
              </div>
              <div
                className="mt-2 bg-black text-green-400 font-mono p-4 rounded-lg h-[20vh] overflow-auto"
                style={{ whiteSpace: "pre-wrap" }} // added styling to preserve newlines
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
                    }`}
                    style={{ color: msg.color, filter: "brightness(3)" }}
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
            className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded"
          >
            Skip Problem
          </button>
        </div>
      </div>
    </div>
  );
}

export default function GamePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <GameContent />
    </Suspense>
  );
}
