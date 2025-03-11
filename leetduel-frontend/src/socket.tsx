"use client";
import { io } from "socket.io-client";

console.log(process.env.SERVER_URL);
const socket = io(process.env.SERVER_URL);
export default socket;
