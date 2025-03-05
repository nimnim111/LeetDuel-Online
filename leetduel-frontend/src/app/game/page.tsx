"use client";
import { useState, useRef, useEffect } from "react";
import { useGame } from "../../context/GameContext";
import { useRouter, useSearchParams } from "next/navigation";
import socket from "../../socket";
import { Fira_Code } from "next/font/google";

const firaCode = Fira_Code({
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});

export default function GamePage() {
  const [consoleOutput, setConsoleOutput] = useState("Console output");
  const [chatMessages, setChatMessages] = useState<string[]>(["Game started!"]);
  const [chatInput, setChatInput] = useState("");
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const { problem, username } = useGame();
  const router = useRouter();
  const searchParams = useSearchParams();
  const party = searchParams.get("party") || "Unknown";

  const starterCode = problem
    ? problem.function_signature +
      `:` +
      `
    # your code here
    return`
    : ``;

  const [code, setCode] = useState(starterCode);

  useEffect(() => {
    if (!problem) {
      router.push("/");
    }
    socket.on("code_submitted", (data) => {
      setConsoleOutput(data.message);
    });

    socket.on("message_received", (data) => {
      setChatMessages((prevMessages) => [
        ...prevMessages,
        `${data.username}: ${data.message}`,
      ]);
    });

    socket.on("player_submit", (data) => {
      setChatMessages((prevMessages) => [...prevMessages, data.message]);
    });

    socket.on("game_over_message", (data) => {
      setChatMessages((prevMessages) => [...prevMessages, data.message]);
    });

    socket.on("game_over", () => {
      // Redirect to Home and pass both party and username as query parameters
      router.push(
        `/?party=${encodeURIComponent(party)}&username=${encodeURIComponent(
          username
        )}`
      );
    });

    return () => {
      socket.off("code_submitted");
      socket.off("message_received");
      socket.off("player_submit");
      socket.off("game_over_message");
      socket.off("game_over");
    };
  }, [problem, router]);

  const lines = code.split("\n");

  const handleScroll = () => {
    if (editorRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = editorRef.current.scrollTop;
    }
  };

  const brackets: Record<string, string> = {
    "{": "}",
    "(": ")",
    "[": "]",
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      setCode(code.substring(0, start) + "    " + code.substring(end));
      setTimeout(() => {
        e.currentTarget.selectionStart = e.currentTarget.selectionEnd =
          start + 4;
      });
    }
    if (["{", "(", "["].includes(e.key)) {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      const newCode =
        code.substring(0, start) +
        e.key +
        brackets[e.key] +
        code.substring(end);
      setCode(newCode);
      setTimeout(() => {
        if (editorRef.current) {
          editorRef.current.focus();
          editorRef.current.setSelectionRange(start + 1, start + 1);
        }
      }, 0);
    }
  };

  const runCode = () => {
    console.log(party);
    console.log(username);
    setConsoleOutput("Running code...");
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

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6 text-gray-900 dark:text-gray-100">
      <div className="max-w-7xl mx-auto" style={{ marginRight: "16.6667%" }}>
        <h1 className="text-4xl font-bold mb-6 text-center">LeetDuel</h1>
        {problem ? (
          <p className="text-xl text-center mb-6">
            Problem: {problem.name} | Difficulty: {problem.difficulty}
          </p>
        ) : (
          <p className="text-xl text-center mb-6">Loading problem...</p>
        )}
        <div className="flex flex-col md:flex-row gap-6">
          <div className="relative md:w-1/2 bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Problem Description</h2>
            <p className="text-md">
              {problem ? problem.description : "Loading problem description..."}
            </p>
            {problem &&
              problem.test_cases &&
              problem.test_cases.slice(0, 3).map((testCase, idx) => (
                <div key={idx} className="mt-4 p-2 border rounded">
                  <p className="font-semibold">Test Case {idx + 1}</p>
                  <p>
                    <span className="font-semibold">Input:</span>{" "}
                    {testCase.input}
                  </p>
                  <p>
                    <span className="font-semibold">Output:</span>{" "}
                    {testCase.output}
                  </p>
                </div>
              ))}
            <button
              onClick={runCode}
              className="absolute bottom-4 right-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
              Run Code
            </button>
          </div>
          <div className="md:w-1/2 flex flex-col">
            <div className="relative flex">
              <div
                ref={lineNumbersRef}
                className={`${firaCode.className} select-none bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 text-right pr-2 rounded-l-lg border border-r-0 border-gray-400 dark:border-gray-500 overflow-hidden`}
                style={{
                  minWidth: "3rem",
                  paddingTop: "1rem",
                  paddingBottom: "0.75rem",
                  lineHeight: "1.5rem",
                }}
              >
                {lines.map((_, idx) => (
                  <div key={idx}>{idx + 1}</div>
                ))}
              </div>
              <textarea
                ref={editorRef}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onScroll={handleScroll}
                onKeyDown={handleKey}
                className={`${firaCode.className} flex-1 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 p-4 rounded-r-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none`}
                rows={15}
              />
            </div>
            <div className="mt-4 bg-black text-green-400 font-mono p-4 rounded-lg h-40 overflow-auto">
              {consoleOutput}
            </div>
          </div>
        </div>
        <div className="fixed top-0 right-0 h-screen w-1/6">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 h-full flex flex-col">
            <h2 className="text-xl font-bold mb-4">Live Chat</h2>
            <div className="flex-1 overflow-y-auto mb-4 space-y-2">
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className="text-sm text-gray-700 dark:text-gray-300 font-mono"
                >
                  {msg}
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
                className="flex-1 px-3 py-2 rounded-l-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
              <button
                onClick={sendMessage}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 rounded-r-lg transition"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
