"""Constants for NAD C 356BEE."""

DOMAIN = "nad_c356bee"
SOURCES = ("CD", "Tuner", "Video", "Disc", "Ipod", "Tape2", "Aux")
BOOL_FIELDS = ("Power", "Mute", "SpeakerA", "SpeakerB", "Tape1")
QUERY_FIELDS = ("Model", *BOOL_FIELDS, "Source")
