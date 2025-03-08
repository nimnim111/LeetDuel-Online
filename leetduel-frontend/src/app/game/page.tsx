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
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const editorContainerRef = useRef<HTMLDivElement>(null);
  const shouldScrollRef = useRef(false);
  const { problem, username } = useGame();
  const router = useRouter();
  const searchParams = useSearchParams();
  const party = searchParams.get("party") || "Unknown";
  const timeLimitParam = searchParams.get("timeLimit");
  const initialTime = timeLimitParam ? parseInt(timeLimitParam, 10) * 60 : 0;
  const [timeLeft, setTimeLeft] = useState(initialTime);
  const [buttonDisabled, setButtonDisabled] = useState(false);

  const starterCode = problem
    ? problem.function_signature +
      `:` +
      `
    # your code here
    return`
    : ``;

  const [code, setCode] = useState(starterCode);
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

  const lines = code.split("\n");

  const brackets: Record<string, string> = {
    "{": "}",
    "(": ")",
    "[": "]",
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const charLength = e.currentTarget.value.length;
    if (
      charLength > 8000 &&
      (/^[a-z0-9]$/i.test(e.key) || e.key === "Enter" || e.key === "Tab")
    ) {
      e.preventDefault();
      return;
    }
    scrollIfAppendedRef.current =
      e.currentTarget.selectionStart === code.length;
    if (e.key === "Tab") {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      setCode(code.substring(0, start) + "    " + code.substring(end));
      setTimeout(() => {
        if (editorRef.current) {
          editorRef.current.focus();
          editorRef.current.setSelectionRange(start + 4, start + 4);
        }
      }, 0);
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
    if (e.key === "Enter") {
      e.preventDefault();
      const target = e.currentTarget;
      const cursor = target.selectionStart;
      const lines = target.value.split("\n");

      let charCount = lines[0].length + 1;
      let indent = 0;
      let lineLength = 0;

      for (let i = 1; i < lines.length; i++) {
        lineLength = lines[i].length + 1;
        if (charCount <= cursor && cursor < charCount + lineLength) {
          indent = Math.floor(
            (lines[i].length - lines[i].trimStart().length) / 4
          );
          if (lines[i].charAt(lineLength - 2) === ":") {
            indent++;
          }
          lineLength = cursor - charCount + 1;
          break;
        }
        charCount += lineLength;
      }
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      setCode(
        code.substring(0, start) +
          "\n" +
          "    ".repeat(indent) +
          code.substring(end)
      );
      charCount += 4 * indent + lineLength;
      setTimeout(() => {
        if (editorRef.current) {
          editorRef.current.focus();
          editorRef.current.setSelectionRange(charCount, charCount);
        }
      }, 0);
    }
  };

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

  return (
    <div
      className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6 text-gray-900 dark:text-gray-100"
      style={{ position: "relative" }}
    >
      <div className="absolute top-0 left-0 m-4 p-2 bg-white dark:bg-gray-800 rounded shadow text-lg font-bold">
        {formatTime(timeLeft)}
      </div>
      <div
        className="max-w-7xl mx-auto h-[75vh]"
        style={{ marginRight: "16.6667%" }}
      >
        <h1 className="text-4xl font-bold mb-6 text-center">LeetDuel</h1>
        {problem ? (
          <p className="text-xl text-center mb-6">
            Problem: {problem.name} | Difficulty: {problem.difficulty}
          </p>
        ) : (
          <p className="text-xl text-center mb-6">Loading problem...</p>
        )}
        <div className="flex flex-col md:flex-row h-full gap-6">
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
              disabled={buttonDisabled}
              className="absolute bottom-4 right-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
              Run Code
            </button>
          </div>
          <div className="md:w-1/2 flex flex-col">
            {/* Begin code editor*/}
            <div
              ref={editorContainerRef}
              className="relative flex h-[55vh] overflow-auto bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg border border-gray-300 dark:border-gray-600"
              onScroll={(e) => {
                if (lineNumbersRef.current) {
                  lineNumbersRef.current.scrollTop = e.currentTarget.scrollTop;
                }
              }}
            >
              <div
                ref={lineNumbersRef}
                className={`${firaCode.className} select-none text-gray-700 p-4 dark:text-gray-300 text-right pr-2 bg-gray-600`}
                style={{
                  minWidth: "3rem",
                  lineHeight: "1.5rem",
                  flexShrink: 0,
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
                onKeyDown={handleKeyDown}
                className={`${firaCode.className} flex-1 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 p-4`}
                wrap="off"
                style={{
                  overflow: "hidden",
                  overflowX: "auto",
                  whiteSpace: "pre",
                }}
              />
            </div>
            {/* End code editor*/}
            <div className="mt-4 bg-black text-green-400 font-mono p-4 rounded-lg h-[20vh] overflow-auto">
              {consoleOutput}
            </div>
          </div>
        </div>
        <div className="fixed top-0 right-0 h-screen w-1/6">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 h-full flex flex-col">
            <h2 className="text-xl font-bold mb-4">Party Chat</h2>
            <div
              ref={chatContainerRef}
              className="flex-1 overflow-y-auto mb-4 space-y-2"
            >
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
      <div className="fixed bottom-0 left-0 m-4">
        <button
          onClick={leaveGame}
          className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
        >
          Leave Game
        </button>
      </div>
    </div>
  );
}
