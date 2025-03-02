"use client";
import React, { createContext, useContext, useState, ReactNode } from "react";

type Problem = { title: string; description: string } | null;

type GameContextType = {
  problem: Problem;
  setProblem: (problem: Problem) => void;
};

const GameContext = createContext<GameContextType | undefined>(undefined);

export function GameProvider({ children }: { children: ReactNode }) {
  const [problem, setProblem] = useState<Problem>(null);
  return (
    <GameContext.Provider value={{ problem, setProblem }}>
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
