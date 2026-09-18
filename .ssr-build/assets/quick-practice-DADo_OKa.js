import { i as boot, t as AppShell } from "../entry-server.js";
import { useEffect, useRef, useState } from "react";
import { ArrowRight, BookOpen, Check, Clock3, Flame, RotateCcw, Target, Trophy, Zap } from "lucide-react";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
//#region frontend/src/quick-practice-data.js
var item = (skill, tip, prompt, options, answer, explanation) => ({
	skill,
	tip,
	prompt,
	options,
	answer,
	explanation
});
var satEla = [
	item("Transitions", "Name the relationship before reading the choices: contrast, cause, or continuation.", "The first prototype used less energy than expected. Its battery life, _____, exceeded the team’s target. Which transition best completes the text?", [
		"however",
		"therefore",
		"instead",
		"nevertheless"
	], 1, "Lower energy use causes longer battery life. “Therefore” signals that result; the other choices suggest a contrast."),
	item("Sentence boundaries", "Check both sides of a punctuation mark for complete sentences.", "The archive opened in June _____ researchers can now consult its letters online. Which choice creates a complete, correctly punctuated sentence?", [
		",",
		";",
		"and",
		"with"
	], 1, "Both sides can stand alone. A semicolon joins two independent clauses. A comma alone creates a comma splice, and “and” would need a comma here."),
	item("Words in context", "Predict a simple replacement, then check it against the whole sentence.", "Although early observations seemed to support the hypothesis, later trials undermined it. As used here, “undermined” most nearly means:", [
		"concealed",
		"expanded",
		"weakened",
		"established"
	], 2, "“Although” sets up a contrast with support. The later trials weakened the hypothesis."),
	item("Evidence", "Reject answers that go beyond the evidence, even if they sound plausible.", "In a study of 120 seedlings, plants receiving six hours of light grew taller on average than plants receiving two hours. Which conclusion is best supported?", [
		"All plants need six hours of light.",
		"More light always causes faster growth.",
		"Two hours of light prevents growth.",
		"The six-hour group was taller on average in this study."
	], 3, "The finding applies to these groups. It does not establish a universal rule or show that the two-hour group did not grow."),
	item("Subject–verb agreement", "Find the grammatical subject; ignore nouns inside interrupting phrases.", "The collection of letters from several explorers _____ a detailed record of the voyage. Which choice completes the sentence correctly?", [
		"provides",
		"provide",
		"have provided",
		"are providing"
	], 0, "The subject is the singular “collection,” not the plural “letters” or “explorers,” so “provides” agrees."),
	item("Rhetorical synthesis", "Read the requested goal first; use only notes that serve it.", "Notes: Lake A is 40 meters deep. Lake B is 65 meters deep. Both lakes contain freshwater. The student wants to emphasize a difference in depth. Which sentence best achieves that goal?", [
		"Both lakes contain freshwater.",
		"Lake B is 25 meters deeper than Lake A.",
		"Lake A and Lake B are both lakes.",
		"Lake B is a freshwater lake 65 meters deep."
	], 1, "65 − 40 = 25. Only this choice directly compares the lakes’ depths."),
	item("Inference", "Prefer the narrow conclusion the text supports over an absolute claim.", "A museum moved a fragile manuscript into a dimmer gallery after conservators observed fading on its pages. What does the text most strongly suggest?", [
		"The manuscript will never fade again.",
		"All other galleries were closed.",
		"The move was intended to limit further damage.",
		"The museum planned to stop displaying manuscripts."
	], 2, "The sequence connects observed fading with a protective change. It supports the intention to reduce damage, not a guarantee or a broader museum policy.")
];
var actEla = [
	item("English · Concision", "Choose the shortest option that preserves the full meaning and correct grammar.", "Choose the most concise replacement for “returned back again” in: After lunch, Maya returned back again to the laboratory.", [
		"returned",
		"returned back",
		"went and returned back",
		"returned again back"
	], 0, "“Returned” already expresses going back. The other choices repeat the same idea."),
	item("English · Agreement", "Cross out the phrase between the subject and verb in your head.", "Choose the correct verb: The results of the experiment _____ consistent across three trials.", [
		"was",
		"is",
		"were",
		"has been"
	], 2, "“Results” is plural. “Of the experiment” does not change the subject, so “were” is correct."),
	item("Reading · Detail", "Locate the exact evidence before relying on what you remember.", "Lena had planned to photograph the harbor at dawn. Thick fog concealed the boats, so she spent the morning sketching the nearby market instead. Why did Lena change her plan?", [
		"The market opened early.",
		"Fog blocked her view of the boats.",
		"Her camera was broken.",
		"The harbor was closed."
	], 1, "The passage explicitly states that thick fog concealed the boats. The other explanations are not given."),
	item("English · Organization", "Use pronouns and time markers to find the sentence’s anchor.", "A paragraph begins: (1) Noor collected water samples from three ponds. (2) She then compared their acidity. (3) The results revealed a clear difference. Where should “Each sample was placed in a labeled container” go?", [
		"Before sentence 1",
		"After sentence 3",
		"After sentence 2",
		"After sentence 1"
	], 3, "The samples must first be collected; labeling them logically precedes comparing their acidity. “Each sample” refers back to sentence 1."),
	item("Reading · Purpose", "Ask what a detail does for the passage, not just what it says.", "The old station once handled hundreds of travelers each day. Now, weeds push through its platform, and the ticket windows stand empty. The details about weeds and empty windows primarily:", [
		"explain train schedules",
		"suggest the station’s decline",
		"describe a recent renovation",
		"criticize travelers"
	], 1, "The details contrast former activity with present disuse and emphasize decline."),
	item("English · Punctuation", "An introductory dependent clause needs a comma before the main clause.", "Choose the correct punctuation: Although the trail was steep _____ the hikers reached the summit before noon.", [
		",",
		";",
		":",
		"."
	], 0, "“Although the trail was steep” is a dependent clause. A comma separates it from the independent main clause."),
	item("Reading · Inference", "Separate a reasonable inference from a claim the passage cannot prove.", "At rehearsal, Eli paused before a difficult passage. After practicing it slowly several times, he played the entire piece without stopping. What is best supported?", [
		"Eli had never played the instrument.",
		"The piece had no difficult passages.",
		"Focused practice helped Eli perform more fluently.",
		"Eli will never make another mistake."
	], 2, "His performance became continuous after targeted practice. The passage supports that improvement without sweeping claims.")
];
function mathBank(exam) {
	const offset = exam === "act" ? 3 : 0;
	return Array.from({ length: 4 }, (_, index) => {
		const n = index + offset + 2;
		return [
			item("Backsolve", "Substitute a promising answer into the original equation; check both sides.", `If 3x + ${n} = ${7 * n}, what is x?`, [
				String(n),
				String(2 * n),
				String(3 * n),
				String(6 * n)
			], 1, `Subtract ${n}: 3x = ${6 * n}. Divide by 3: x = ${2 * n}. Substitution gives ${6 * n} + ${n} = ${7 * n}.`),
			item("Percent multipliers", "A percent decrease multiplies by 1 minus the decimal rate. Do not subtract the rate itself.", `A jacket costs $${20 * n}. Its price is reduced by 25%. What is the sale price?`, [
				`$${5 * n}`,
				`$${19 * n}`,
				`$${25 * n}`,
				`$${15 * n}`
			], 3, `Keep 75% of the price: 0.75 × ${20 * n} = ${15 * n}. The discount itself is $${5 * n}.`),
			item("Read the target", "Circle what the question actually asks. You may not need to solve for the variable.", `If 4x + ${n} = ${9 * n}, what is the value of 8x?`, [
				String(16 * n),
				String(2 * n),
				String(8 * n),
				String(18 * n)
			], 0, `Subtract ${n} to get 4x = ${8 * n}. Double both sides: 8x = ${16 * n}. You do not need to calculate x.`),
			item("Rate setup", "Write the units with the numbers so they cancel in the right direction.", `A machine produces ${12 * n} parts in 3 minutes at a constant rate. How many parts does it produce in 5 minutes?`, [
				String(12 * n + 2),
				String(4 * n),
				String(20 * n),
				String(60 * n)
			], 2, `${12 * n} ÷ 3 = ${4 * n} parts per minute. Multiply by 5 minutes to get ${20 * n} parts.`),
			item(exam === "sat" ? "Equivalent expressions" : "Math · Distribution", "Distribute to every term, then combine like terms. Check with a simple input if uncertain.", `Which expression is equivalent to ${n}(x + 3) − 2x?`, [
				`${n - 2}x + 3`,
				`${n + 2}x + ${3 * n}`,
				`${n - 2}x + ${3 * n}`,
				`${n}x + ${3 * n - 2}`
			], 2, `Distribute ${n}: ${n}x + ${3 * n} − 2x. Combining the x terms gives ${n - 2}x + ${3 * n}.`),
			item("Average shortcut", "Convert an average to a total before finding the missing value.", `Four numbers have an average of ${5 * n}. Three of the numbers are ${2 * n}, ${4 * n}, and ${6 * n}. What is the fourth?`, [
				String(5 * n),
				String(8 * n),
				String(12 * n),
				String(20 * n)
			], 1, `The total is 4 × ${5 * n} = ${20 * n}. The three known numbers total ${12 * n}, leaving ${8 * n}.`)
		];
	}).flat();
}
var drillBanks = {
	sat: {
		math: mathBank("sat"),
		ela: satEla
	},
	act: {
		math: mathBank("act"),
		ela: actEla
	}
};
function makeRound(exam, subject) {
	const pool = [...drillBanks[exam][subject]];
	for (let i = pool.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[pool[i], pool[j]] = [pool[j], pool[i]];
	}
	return pool.filter((question, index) => pool.findIndex((other) => other.skill === question.skill) === index).slice(0, 5).map((question) => {
		const choices = question.options.map((text, index) => ({
			text,
			correct: index === question.answer
		}));
		for (let i = choices.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[choices[i], choices[j]] = [choices[j], choices[i]];
		}
		return {
			...question,
			options: choices.map((choice) => choice.text),
			answer: choices.findIndex((choice) => choice.correct)
		};
	});
}
//#endregion
//#region frontend/src/quick-practice.jsx
var labels = {
	sat: {
		math: "Math",
		ela: "Reading & Writing"
	},
	act: {
		math: "Math",
		ela: "English & Reading"
	}
};
var formatTime = (seconds) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
function QuickPractice() {
	const [exam, setExam] = useState("sat");
	const [subject, setSubject] = useState("math");
	const [mode, setMode] = useState("sprint");
	const [round, setRound] = useState(null);
	const [answers, setAnswers] = useState([]);
	const [selected, setSelected] = useState(null);
	const [revealed, setRevealed] = useState(false);
	const [hint, setHint] = useState(false);
	const [seconds, setSeconds] = useState(0);
	const [finished, setFinished] = useState(false);
	const [review, setReview] = useState(false);
	const started = useRef(0);
	const questionHeading = useRef(null);
	const index = answers.length - (revealed ? 1 : 0);
	const question = round?.[index];
	const correct = answers.filter((answer) => answer.correct).length;
	const streak = answers.reduce((run, answer) => answer.correct ? run + 1 : 0, 0);
	const bestStreak = answers.reduce((state, answer) => {
		const current = answer.correct ? state.current + 1 : 0;
		return {
			current,
			best: Math.max(state.best, current)
		};
	}, {
		current: 0,
		best: 0
	}).best;
	const points = answers.reduce((sum, answer) => sum + (answer.correct ? answer.hint ? 50 : 100 : 0), 0);
	useEffect(() => {
		if (!round || finished) return;
		const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - started.current) / 1e3)), 500);
		return () => window.clearInterval(timer);
	}, [round, finished]);
	useEffect(() => {
		if (round) questionHeading.current?.focus();
	}, [
		round,
		index,
		finished,
		review
	]);
	const start = (questions = makeRound(exam, subject)) => {
		setRound(questions);
		setAnswers([]);
		setSelected(null);
		setRevealed(false);
		setHint(false);
		setFinished(false);
		setReview(false);
		setSeconds(0);
		started.current = Date.now();
	};
	const check = () => {
		if (selected === null || revealed) return;
		setAnswers((previous) => [...previous, {
			question,
			selected,
			correct: selected === question.answer,
			hint
		}]);
		setRevealed(true);
	};
	const next = () => {
		if (answers.length === round.length) {
			setSeconds(Math.floor((Date.now() - started.current) / 1e3));
			setFinished(true);
		} else {
			setSelected(null);
			setRevealed(false);
			setHint(false);
		}
	};
	const reset = () => {
		setRound(null);
		setFinished(false);
		setReview(false);
	};
	const missed = answers.filter((answer) => !answer.correct);
	return /* @__PURE__ */ jsx(AppShell, {
		name: boot.data.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: `app-main quick-prep ${round ? "prep-in-round" : ""}`,
			children: [/* @__PURE__ */ jsxs("header", {
				className: "prep-heading",
				children: [/* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsxs("div", {
						className: "eyebrow",
						children: [/* @__PURE__ */ jsx("span", {}), " TEST PREP / QUICK PRACTICE"]
					}),
					/* @__PURE__ */ jsx("h1", { children: round ? "Make your move." : "Get into your rhythm." }),
					/* @__PURE__ */ jsx("p", { children: round ? "One question. One strategy. A sharper next attempt." : "A little focus today. A little more confidence on test day." })
				] }), /* @__PURE__ */ jsxs("a", {
					href: "/dashboard/test-path-view",
					className: "prep-path-link",
					children: ["My study path ", /* @__PURE__ */ jsx(ArrowRight, { size: 16 })]
				})]
			}), !round ? /* @__PURE__ */ jsxs(Fragment, { children: [
				/* @__PURE__ */ jsxs("section", {
					className: "prep-config",
					"aria-label": "Choose your practice",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "prep-config-title",
							children: [/* @__PURE__ */ jsx("span", {
								className: "prep-step-tag",
								children: "01"
							}), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h2", { children: "Make it your session." }), /* @__PURE__ */ jsx("p", { children: "Pick your exam, your focus, and your pace." })] })]
						}),
						/* @__PURE__ */ jsx("div", {
							className: "prep-section-heading",
							children: /* @__PURE__ */ jsx("span", { children: "EXAM" })
						}),
						/* @__PURE__ */ jsx("div", {
							className: "prep-exams",
							role: "group",
							"aria-label": "Exam",
							children: ["sat", "act"].map((value) => /* @__PURE__ */ jsxs("button", {
								type: "button",
								"aria-pressed": exam === value,
								onClick: () => setExam(value),
								className: exam === value ? "is-selected" : "",
								children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: value.toUpperCase() }), /* @__PURE__ */ jsx("small", { children: value === "sat" ? "Math · Reading & Writing" : "Math · English & Reading" })] }), /* @__PURE__ */ jsx("span", {
									className: "prep-selection-dot",
									children: exam === value && /* @__PURE__ */ jsx(Check, { size: 15 })
								})]
							}, value))
						}),
						/* @__PURE__ */ jsx("div", {
							className: "prep-section-heading",
							children: /* @__PURE__ */ jsx("span", { children: "FOCUS" })
						}),
						/* @__PURE__ */ jsx("div", {
							className: "prep-subjects",
							role: "group",
							"aria-label": "Subject",
							children: [[
								"math",
								"Math",
								Target
							], [
								"ela",
								"ELA",
								BookOpen
							]].map(([value, label, Icon]) => /* @__PURE__ */ jsxs("button", {
								type: "button",
								"aria-pressed": subject === value,
								onClick: () => setSubject(value),
								className: subject === value ? "is-selected" : "",
								children: [
									/* @__PURE__ */ jsx(Icon, {}),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: label }), /* @__PURE__ */ jsx("small", { children: value === "math" ? "Numbers & problem solving" : labels[exam][value] })] }),
									subject === value && /* @__PURE__ */ jsx(Check, { size: 17 })
								]
							}, value))
						}),
						/* @__PURE__ */ jsx("div", {
							className: "prep-section-heading",
							children: /* @__PURE__ */ jsx("span", { children: "PACE" })
						}),
						/* @__PURE__ */ jsx("div", {
							className: "prep-modes",
							role: "group",
							"aria-label": "Practice mode",
							children: [[
								"sprint",
								"Speed round",
								"Aim for five minutes. Keep going if you need more.",
								Zap
							], [
								"learn",
								"Strategy practice",
								"No clock on screen. Work through each tactic.",
								BookOpen
							]].map(([value, title, copy, Icon]) => /* @__PURE__ */ jsxs("button", {
								type: "button",
								"aria-pressed": mode === value,
								onClick: () => setMode(value),
								className: mode === value ? "is-selected" : "",
								children: [
									/* @__PURE__ */ jsx(Icon, {}),
									/* @__PURE__ */ jsx("b", { children: title }),
									/* @__PURE__ */ jsx("small", { children: copy })
								]
							}, value))
						})
					]
				}),
				/* @__PURE__ */ jsxs("aside", {
					className: "prep-launch",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "prep-launch-top",
							children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("i", {}), " READY WHEN YOU ARE"] }), /* @__PURE__ */ jsx(Zap, { size: 20 })]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "prep-orbit",
							"aria-hidden": "true",
							children: [
								/* @__PURE__ */ jsx("i", {}),
								/* @__PURE__ */ jsx("i", {}),
								/* @__PURE__ */ jsxs("span", { children: ["05", /* @__PURE__ */ jsx("small", { children: "QUESTIONS" })] }),
								/* @__PURE__ */ jsx("b", { children: /* @__PURE__ */ jsx(Zap, { size: 19 }) })
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "prep-launch-copy",
							children: [
								/* @__PURE__ */ jsxs("span", {
									className: "prep-exam-chip",
									children: [
										exam.toUpperCase(),
										" / ",
										labels[exam][subject]
									]
								}),
								/* @__PURE__ */ jsx("h2", { children: mode === "sprint" ? "Find your fast." : "Learn the move." }),
								/* @__PURE__ */ jsx("p", { children: mode === "sprint" ? "Beat the trap. Build your streak. Turn five focused minutes into real practice." : "Slow it down. Learn a useful shortcut, then put it to work on the next question." })
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "prep-launch-metrics",
							children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Clock3, { size: 15 }), mode === "sprint" ? "5-minute target" : "No timer pressure"] }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Flame, { size: 15 }), "Streaks + points"] })]
						}),
						/* @__PURE__ */ jsxs("button", {
							className: "button button--primary",
							onClick: () => start(),
							children: [
								"Start ",
								mode === "sprint" ? "speed round" : "practicing",
								" ",
								/* @__PURE__ */ jsx(ArrowRight, {})
							]
						}),
						/* @__PURE__ */ jsx("small", { children: "Original strategy drills / Instant explanations" })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "prep-bottom",
					"aria-label": "Keep building",
					children: [/* @__PURE__ */ jsxs("a", {
						className: "prep-long-path",
						href: `/dashboard/test-path-builder?test_focus=${exam}&subject_focus=${subject}`,
						children: [
							/* @__PURE__ */ jsx("span", {
								className: "prep-path-icon",
								children: /* @__PURE__ */ jsx(BookOpen, {})
							}),
							/* @__PURE__ */ jsxs("span", { children: [
								/* @__PURE__ */ jsx("small", { children: "THE LONG GAME" }),
								/* @__PURE__ */ jsx("b", { children: "Build a stronger foundation." }),
								/* @__PURE__ */ jsx("p", { children: "Lessons and a study plan shaped around you." })
							] }),
							/* @__PURE__ */ jsx(ArrowRight, {})
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "prep-how",
						children: [
							/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "01" }), " Try a tactic"] }),
							/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "02" }), " Get feedback"] }),
							/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "03" }), " Retry the miss"] })
						]
					})]
				}),
				/* @__PURE__ */ jsxs("p", {
					className: "prep-fine-print",
					children: ["Round points: 100 per correct answer, or 50 with a hint. Separate from account points. These short drills are not full test simulations.", exam === "act" ? " Find Science in the full ACT study path." : ""]
				})
			] }) : /* @__PURE__ */ jsxs("section", {
				className: "prep-session",
				"aria-label": `${exam.toUpperCase()} ${labels[exam][subject]} practice`,
				children: [/* @__PURE__ */ jsxs("div", {
					className: "prep-session-bar",
					children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsxs("span", {
						className: "prep-session-kicker",
						children: ["MENTICS PRACTICE / ", mode === "sprint" ? "SPEED" : "STRATEGY"]
					}), /* @__PURE__ */ jsxs("strong", { children: [
						/* @__PURE__ */ jsx("b", { children: exam.toUpperCase() }),
						" ",
						labels[exam][subject]
					] })] }), /* @__PURE__ */ jsx("button", {
						className: "text-button",
						onClick: reset,
						children: finished ? "Change practice" : "End round"
					})]
				}), finished ? /* @__PURE__ */ jsxs("div", {
					className: "prep-results",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "prep-result-mark",
							children: [/* @__PURE__ */ jsx(Trophy, { className: "prep-trophy" }), /* @__PURE__ */ jsxs("span", { children: [
								"ROUND",
								/* @__PURE__ */ jsx("br", {}),
								"COMPLETE"
							] })]
						}),
						/* @__PURE__ */ jsx("div", {
							className: "eyebrow",
							children: "YOUR PRACTICE RECEIPT"
						}),
						/* @__PURE__ */ jsx("h2", {
							ref: questionHeading,
							tabIndex: -1,
							children: correct === round.length ? "Clean sweep." : "The next move is clear."
						}),
						/* @__PURE__ */ jsxs("p", { children: [
							correct,
							" of ",
							round.length,
							" correct",
							mode === "sprint" ? ` in ${formatTime(seconds)}` : "",
							". ",
							missed.length ? "Bring the misses back for another rep." : "Keep the momentum with another set."
						] }),
						/* @__PURE__ */ jsxs("div", {
							className: "prep-result-stats",
							children: [
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "ROUND POINTS" }), /* @__PURE__ */ jsx("b", { children: points })] }),
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "ACCURACY" }), /* @__PURE__ */ jsxs("b", { children: [Math.round(correct / round.length * 100), "%"] })] }),
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "BEST STREAK" }), /* @__PURE__ */ jsx("b", { children: bestStreak })] })
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "prep-result-actions",
							children: [
								/* @__PURE__ */ jsxs("button", {
									className: "button button--primary",
									onClick: () => start(),
									children: ["New round ", /* @__PURE__ */ jsx(ArrowRight, {})]
								}),
								missed.length > 0 && /* @__PURE__ */ jsxs("button", {
									className: "button button--quiet",
									onClick: () => start(missed.map((answer) => answer.question)),
									children: [
										/* @__PURE__ */ jsx(RotateCcw, {}),
										" Retry ",
										missed.length,
										" missed"
									]
								}),
								/* @__PURE__ */ jsxs("button", {
									className: "text-button",
									"aria-expanded": review,
									onClick: () => setReview(!review),
									children: [review ? "Hide" : "Review", " answers"]
								})
							]
						}),
						review && /* @__PURE__ */ jsx("div", {
							className: "prep-review",
							children: answers.map((answer, i) => /* @__PURE__ */ jsxs("article", { children: [
								/* @__PURE__ */ jsxs("small", { children: [
									answer.correct ? "CORRECT" : "PRACTICE AGAIN",
									" · ",
									answer.question.skill
								] }),
								/* @__PURE__ */ jsx("h3", { children: answer.question.prompt }),
								/* @__PURE__ */ jsxs("p", { children: ["Your answer: ", answer.question.options[answer.selected]] }),
								/* @__PURE__ */ jsxs("b", { children: ["Correct answer: ", answer.question.options[answer.question.answer]] }),
								/* @__PURE__ */ jsx("p", { children: answer.question.explanation })
							] }, i))
						})
					]
				}) : /* @__PURE__ */ jsxs(Fragment, { children: [
					/* @__PURE__ */ jsxs("div", {
						className: "prep-hud",
						children: [
							/* @__PURE__ */ jsxs("span", {
								className: "prep-round-count",
								children: [/* @__PURE__ */ jsx("small", { children: "QUESTION" }), /* @__PURE__ */ jsxs("b", { children: [String(index + 1).padStart(2, "0"), /* @__PURE__ */ jsxs("i", { children: ["/ ", String(round.length).padStart(2, "0")] })] })]
							}),
							/* @__PURE__ */ jsxs("span", { children: [
								/* @__PURE__ */ jsx(Flame, {}),
								" ",
								streak,
								" streak"
							] }),
							/* @__PURE__ */ jsxs("span", { children: [
								/* @__PURE__ */ jsx(Zap, {}),
								" ",
								points,
								" pts"
							] }),
							mode === "sprint" && /* @__PURE__ */ jsxs("span", { children: [
								/* @__PURE__ */ jsx(Clock3, {}),
								" ",
								formatTime(seconds),
								" ",
								/* @__PURE__ */ jsx("small", { children: "/ 5:00 target" })
							] })
						]
					}),
					/* @__PURE__ */ jsx("div", {
						className: "prep-progress",
						role: "progressbar",
						"aria-label": "Questions answered",
						"aria-valuenow": answers.length,
						"aria-valuemin": 0,
						"aria-valuemax": round.length,
						children: /* @__PURE__ */ jsx("i", { style: { width: `${answers.length / round.length * 100}%` } })
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "prep-question",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "prep-question-meta",
								children: [/* @__PURE__ */ jsx("div", {
									className: "eyebrow",
									children: question.skill
								}), /* @__PURE__ */ jsx("span", { children: mode === "sprint" ? "MAKE THE CALL" : "WORK THE MOVE" })]
							}),
							/* @__PURE__ */ jsx("h2", {
								ref: questionHeading,
								tabIndex: -1,
								children: question.prompt
							}),
							/* @__PURE__ */ jsx("div", {
								className: "prep-answers",
								role: "group",
								"aria-label": "Answer choices",
								children: question.options.map((option, i) => /* @__PURE__ */ jsxs("button", {
									type: "button",
									disabled: revealed,
									"aria-pressed": selected === i,
									onClick: () => setSelected(i),
									className: `${selected === i ? "is-selected" : ""} ${revealed && i === question.answer ? "is-correct" : ""} ${revealed && selected === i && i !== question.answer ? "is-wrong" : ""}`,
									children: [
										/* @__PURE__ */ jsx("span", { children: "ABCD"[i] }),
										/* @__PURE__ */ jsx("b", { children: option }),
										revealed && i === question.answer && /* @__PURE__ */ jsx(Check, { "aria-label": "Correct answer" })
									]
								}, i))
							}),
							!revealed && /* @__PURE__ */ jsxs("button", {
								className: "text-button prep-hint-button",
								"aria-expanded": hint,
								onClick: () => setHint(true),
								disabled: hint,
								children: [/* @__PURE__ */ jsx(Zap, { size: 16 }), " Show strategy hint · correct answer earns 50 pts"]
							}),
							hint && !revealed && /* @__PURE__ */ jsxs("div", {
								className: "prep-feedback",
								children: [/* @__PURE__ */ jsx("b", { children: "The move" }), /* @__PURE__ */ jsx("p", { children: question.tip })]
							}),
							revealed && /* @__PURE__ */ jsxs("div", {
								className: `prep-feedback ${selected === question.answer ? "is-correct" : ""}`,
								role: "status",
								children: [
									/* @__PURE__ */ jsx("b", { children: selected === question.answer ? "Correct. Keep that move." : `The answer is ${"ABCD"[question.answer]}. Here’s why.` }),
									/* @__PURE__ */ jsx("p", { children: question.explanation }),
									/* @__PURE__ */ jsxs("small", { children: [
										/* @__PURE__ */ jsx("strong", { children: "Test-day tactic:" }),
										" ",
										question.tip
									] })
								]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "prep-question-actions",
								children: [/* @__PURE__ */ jsx("span", { children: mode === "sprint" ? "Accuracy first. Speed follows." : "Understand the move before moving on." }), revealed ? /* @__PURE__ */ jsxs("button", {
									className: "button button--primary",
									onClick: next,
									children: [
										answers.length === round.length ? "See results" : "Next question",
										" ",
										/* @__PURE__ */ jsx(ArrowRight, {})
									]
								}) : /* @__PURE__ */ jsxs("button", {
									className: "button button--primary",
									disabled: selected === null,
									onClick: check,
									children: ["Check answer ", /* @__PURE__ */ jsx(Check, {})]
								})]
							})
						]
					})
				] })]
			})]
		})
	});
}
//#endregion
export { QuickPractice as default };
