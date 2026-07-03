import { InputHTMLAttributes, useState } from "react";

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type">;

export function PasswordInput(props: PasswordInputProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span className="password-field">
      <input {...props} type={isVisible ? "text" : "password"} />
      <button
        aria-label={isVisible ? "Hide password" : "Show password"}
        aria-pressed={isVisible}
        className="password-visibility-button"
        onClick={() => setIsVisible((current) => !current)}
        type="button"
      >
        <svg aria-hidden="true" fill="none" viewBox="0 0 24 24">
          <path
            d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.8"
          />
          <path
            d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.8"
          />
          {isVisible && (
            <path
              d="M4 4l16 16"
              stroke="currentColor"
              strokeLinecap="round"
              strokeWidth="2"
            />
          )}
        </svg>
      </button>
    </span>
  );
}
