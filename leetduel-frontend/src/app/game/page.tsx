"use client";
import { useState, useRef, useEffect } from "react";
import { useGame } from "../../context/GameContext";
import { useRouter, useSearchParams } from "next/navigation";
import socket from "../../socket";

const starterCode = `def run():
    # your code here
    return`;

export default function GamePage() {
  const [code, setCode] = useState(starterCode);
  const [consoleOutput, setConsoleOutput] = useState("Console output...");
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const { problem, username } = useGame();
  const router = useRouter();
  const searchParams = useSearchParams();
  const party = searchParams.get("party") || "Unknown";

  useEffect(() => {
    if (!problem) {
      router.push("/");
    }
    socket.on("code_submitted", (data) => {
      setConsoleOutput(data.message);
    });
    return () => {
      socket.off("code_submitted");
    };
  }, [problem, router]);

  const lines = code.split("\n");

  const handleScroll = () => {
    if (editorRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = editorRef.current.scrollTop;
    }
  };

  const handleTab = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
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
  };

  // Simulate running code
  const runCode = () => {
    console.log(party);
    console.log(problem.title);
    console.log(username);
    setConsoleOutput("Running code...");
    socket.emit("submit_code", {
      code: code,
      party_code: party,
      username: username,
    });
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6 text-gray-900 dark:text-gray-100">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-6 text-center">
          LeetDuel Game {party}
        </h1>
        {problem ? (
          <p className="text-xl text-center mb-6">
            Problem: {problem.title} {username && `| User: ${username}`}
          </p>
        ) : (
          <p className="text-xl text-center mb-6">Loading problem...</p>
        )}
        <div className="flex flex-col md:flex-row gap-6">
          {/* Updated Problem Description Container with Run Code button */}
          <div className="relative md:w-1/2 bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Problem Description</h2>
            <p className="text-md">
              {problem ? problem.description : "Loading problem description..."}
            </p>
            <p className="mt-4 text-sm text-gray-500">
              Hint: Use a hash map to track the needed complement.
            </p>
            <button
              onClick={runCode}
              className="absolute bottom-4 right-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
              Run Code
            </button>
          </div>
          {/* Code Editor and Console */}
          <div className="md:w-1/2 flex flex-col">
            {/* Code Editor with line numbers */}
            <div className="relative flex">
              <div
                ref={lineNumbersRef}
                className="select-none bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 text-right pr-2 rounded-l-lg border border-r-0 border-gray-400 dark:border-gray-500 overflow-hidden"
                style={{
                  minWidth: "3rem",
                  paddingTop: "1rem",
                  paddingBottom: "0.75rem",
                  lineHeight: "1.5rem",
                  fontFamily: "monospace",
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
                onKeyDown={handleTab}
                className="flex-1 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-mono p-4 rounded-r-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={15}
              />
            </div>
            {/* Removed previous Run Code button from here */}
            <div className="mt-4 bg-black text-green-400 font-mono p-4 rounded-lg h-40 overflow-auto">
              {consoleOutput}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
