"use client";
import React, { createContext, useContext, useState, ReactNode } from "react";
import { Problem, GameContextType } from "../types";

const GameContext = createContext<GameContextType | undefined>(undefined);

export function GameProvider({ children }: { children: ReactNode }) {
  const [problem, setProblem] = useState<Problem>(null);
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
  const context = useContext(GameContext);
  if (!context) {
    throw new Error("useGame must be used within a GameProvider");
  }
  return context;
}
