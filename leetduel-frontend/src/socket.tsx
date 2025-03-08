"use client";
import { io } from "socket.io-client";

const socket = io("https://leetduel-production.up.railway.app/");
export default socket;
