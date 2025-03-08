"use client";
import { io } from "socket.io-client";

const socket = io("http://leetduel-production.up.railway.app");
export default socket;
