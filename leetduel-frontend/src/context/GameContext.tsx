"use client";
import React, { createContext, useContext, useState } from "react";

interface GameContextType {
  problem: any;
  setProblem: (problem: any) => void;
  partyCode: string;
  setPartyCode: (code: string) => void;
  username: string;
  setUsername: (name: string) => void;
}

const GameContext = createContext<GameContextType>({
  problem: null,
  setProblem: () => {},
  partyCode: "",
  setPartyCode: () => {},
  username: "",
  setUsername: () => {},
});

export function GameProvider({ children }: { children: React.ReactNode }) {
  const [problem, setProblem] = useState<any>(null);
  const [partyCode, setPartyCode] = useState("");
  const [username, setUsername] = useState("");

  return (
    <GameContext.Provider
      value={{
        problem,
        setProblem,
        partyCode,
        setPartyCode,
        username,
        setUsername,
      }}
    >
      {children}
    </GameContext.Provider>
  );
}

export function useGame() {
  return useContext(GameContext);
}
