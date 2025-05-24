#!/usr/bin/env python3
"""
Live Transcription with Speaker Diarization using AssemblyAI Python SDK
Based on the working example but with speaker diarization enabled
"""

import assemblyai as aai
from colorama import init, Fore, Style
from datetime import datetime
import os

# Initialize colorama for colored terminal output
init(autoreset=True)

# Speaker colors for terminal display
SPEAKER_COLORS = {
    "A": Fore.CYAN,
    "B": Fore.GREEN,
    "C": Fore.YELLOW,
    "D": Fore.MAGENTA,
    "E": Fore.RED,
    "F": Fore.BLUE,
    "G": Fore.LIGHTCYAN_EX,
    "H": Fore.LIGHTGREEN_EX,
}


def get_speaker_color(speaker):
    """Get color for speaker label"""
    return SPEAKER_COLORS.get(speaker, Fore.WHITE)


def display_transcript_with_speakers(transcript):
    """Display transcript with speaker diarization"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Check if we have word-level data with speakers
    if hasattr(transcript, "words") and transcript.words:
        # Group consecutive words by speaker
        current_speaker = None
        current_text = []

        for word in transcript.words:
            speaker = getattr(word, "speaker", None)

            if speaker != current_speaker:
                # Display previous speaker's text if any
                if current_text and current_speaker is not None:
                    speaker_color = get_speaker_color(current_speaker)
                    print(
                        f"{Fore.BLUE}[{timestamp}] {speaker_color}Speaker {current_speaker}: {Fore.WHITE}{' '.join(current_text)}"
                    )
                    current_text = []

                current_speaker = speaker

            if hasattr(word, "text"):
                current_text.append(word.text)

        # Display remaining text
        if current_text and current_speaker is not None:
            speaker_color = get_speaker_color(current_speaker)
            print(
                f"{Fore.BLUE}[{timestamp}] {speaker_color}Speaker {current_speaker}: {Fore.WHITE}{' '.join(current_text)}"
            )
    else:
        # Fallback to regular transcript without speaker info
        print(f"{Fore.BLUE}[{timestamp}] {Fore.WHITE}{transcript.text}")


def on_open(session_opened: aai.RealtimeSessionOpened):
    """This function is called when the connection has been established."""
    print(f"{Fore.GREEN}✓ Session ID: {session_opened.session_id}")
    print(f"{Fore.GREEN}✓ Speaker diarization enabled")
    print(f"{Fore.CYAN}🎙️ Start speaking...")


def on_data(transcript: aai.RealtimeTranscript):
    """This function is called when a new transcript has been received."""
    if not transcript.text:
        return

    if isinstance(transcript, aai.RealtimeFinalTranscript):
        # Final transcript - check for speaker diarization
        display_transcript_with_speakers(transcript)
    else:
        # Partial transcript (live) - show without speaker info
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(
            f"{Fore.BLUE}[{timestamp}] {Fore.YELLOW}[LIVE] {Fore.WHITE}{transcript.text}",
            end="\r",
        )


def on_error(error: aai.RealtimeError):
    """This function is called when an error occurs."""
    print(f"{Fore.RED}❌ An error occurred: {error}")


def on_close():
    """This function is called when the connection has been closed."""
    print(f"\n{Fore.YELLOW}🛑 Closing Session")


def main():
    # Get API key
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        print(f"{Fore.YELLOW}Please enter your AssemblyAI API key:")
        api_key = input("API Key: ").strip()
        if not api_key:
            print(f"{Fore.RED}❌ API key is required!")
            return

    # Set the API key
    aai.settings.api_key = api_key

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🎤 LIVE TRANSCRIPTION WITH SPEAKER DIARIZATION 🎤")
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.WHITE}Press CTRL+C to stop")

    # Create the Real-Time transcriber with speaker diarization
    transcriber = aai.RealtimeTranscriber(
        sample_rate=44_100,
        speaker_labels=True,  # Enable speaker diarization
        word_boost=["um", "uh", "hmm", "okay", "right"],  # Boost common words
        boost_param="high",
        on_data=on_data,
        on_error=on_error,
        on_open=on_open,
        on_close=on_close,
    )

    try:
        # Start the connection
        transcriber.connect()

        # Open a microphone stream
        microphone_stream = aai.extras.MicrophoneStream()

        # Press CTRL+C to abort
        transcriber.stream(microphone_stream)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping transcription...")
    finally:
        transcriber.close()
        print(f"{Fore.CYAN}👋 Goodbye!")


if __name__ == "__main__":
    main()
