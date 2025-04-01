import React, { useState } from "react";

const Spinner = () => (
  <div className="flex items-center justify-center">
    <svg
      width="24"
      height="24"
      stroke="#fff"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <style>{`
                  .spinner_V8m1{transform-origin:center;animation:spinner_zKoa 2s linear infinite}
                  .spinner_V8m1 circle{stroke-linecap:round;animation:spinner_YpZS 1.5s ease-in-out infinite}
                  @keyframes spinner_zKoa{100%{transform:rotate(360deg)}}
                  @keyframes spinner_YpZS{
                      0%{stroke-dasharray:0 150;stroke-dashoffset:0}
                      47.5%{stroke-dasharray:42 150;stroke-dashoffset:-16}
                      95%,100%{stroke-dasharray:42 150;stroke-dashoffset:-59}
                  }
              `}</style>
      <g className="spinner_V8m1">
        <circle cx="12" cy="12" r="9.5" fill="none" strokeWidth="3"></circle>
      </g>
    </svg>
  </div>
);

interface ButtonProps {
  loading: boolean;
  setLoading: (state: boolean) => void;
  handleClick: () => void;
  children: React.ReactNode;
  color: string;
}

const Button: React.FC<ButtonProps> = ({
  loading,
  setLoading,
  handleClick,
  color,
  children,
}) => {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      disabled={loading}
      onClick={() => {
        setLoading(true);
        handleClick();
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        backgroundColor: hovered ? color : undefined,
        borderColor: hovered ? color : undefined,
      }}
      className="w-full bg-transparent border-2 border-gray-300 text-white py-3 rounded-lg transition duration-500 cursor-pointer"
    >
      {loading ? <Spinner /> : children}
    </button>
  );
};

export default Button;
