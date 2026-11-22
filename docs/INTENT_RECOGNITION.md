# Intent Recognition

## Purpose

The intent recognizer routes learner messages into a small set of interaction
categories. It does not assess correctness, infer ability, diagnose a learner,
or change lesson progression.

## Intents

| Intent | Meaning | Routing |
| --- | --- | --- |
| ANSWER_SUBMISSION | A response intended for the current exercise | Pass to the authoritative answer verifier |
| QUESTION | A content or process question | Answer or clarify without grading it as an exercise response |
| HINT_REQUEST | An explicit request for a hint | Use the curriculum's authored hint |
| CONFUSION | An explicit statement that the learner is confused or stuck | Ask one concise clarifying/guiding question |
| EXPLANATION_REQUEST | A request for an explanation or a different explanation | Provide an explanation without changing lesson state |
| UNCERTAIN | Empty or unclassifiable input | Ask the learner to rephrase |

## Current implementation

IntentRecognizer is dependency-free and rule-based. Explicit requests are
checked before generic question language. Non-empty unmatched text defaults to
ANSWER_SUBMISSION, which means only that it should be passed to the answer
verifier. It does not mean the message is a valid or correct answer.

The result includes a confidence value and short evidence labels for
inspection. These values are routing metadata, not calibrated probabilities.

NoggimigoIntentAI.predict_intent remains as a compatibility facade for older
experimental callers. New code should use IntentRecognizer.classify.

## Safety and correctness boundaries

- Intent recognition never marks an answer correct or incorrect.
- Only answer_verifier.verify_answer may determine answer correctness.
- Intent recognition never advances the lesson.
- Ambiguous or unsupported messages must not be silently treated as correct.
- The classifier does not infer emotion, disability, intelligence, attention,
  motivation, or mastery.
- The initial rule set is a baseline and must be evaluated on held-out,
  representative learner messages before being described as accurate.

## Known limitations

Rule-based patterns can miss paraphrases and can confuse mixed messages. For
example, a learner may submit an answer and ask a question in the same sentence.
The first version returns one primary route and does not yet support multi-intent
messages or confidence calibration. Session-level routing and response
generation are separate integration work.
