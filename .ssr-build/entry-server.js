import { renderToString } from "react-dom/server";
import { Component, Suspense, lazy, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import DOMPurify from "dompurify";
import { marked } from "marked";
import { Toaster, toast } from "sonner";
import { AlertTriangle, ArrowLeft, ArrowRight, Award, BarChart3, BookOpen, Brain, CalendarDays, Check, Clock3, Flag, Flame, GraduationCap, Hand, Headphones, House, LayoutDashboard, LineChart, LockKeyhole, LogOut, Mail, Menu, MessageCircle, PenLine, Plus, RotateCcw, Search, Send, Settings, ShieldCheck, SkipForward, Sparkles, Swords, Target, Trophy, UserRound, UsersRound, X, Zap } from "lucide-react";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
//#region frontend/src/boot.js
var initial = typeof window !== "undefined" && window.__MENTICS__ ? window.__MENTICS__ : {
	page: "landing",
	data: {}
};
var boot = {
	page: initial.page || "landing",
	data: initial.data || {}
};
function setBoot(next) {
	boot.page = next && next.page || "landing";
	boot.data = next && next.data || {};
}
//#endregion
//#region frontend/src/home-hero.jsx
var previews = {
	SAT: {
		title: "Make the next point count.",
		focus: "Master linear equations",
		subject: "Math · Focused practice",
		steps: [
			"Find your starting point",
			"Learn the strategy",
			"Practice with purpose",
			"Understand every miss",
			"Build your next path"
		],
		icon: Target
	},
	ACT: {
		title: "Find your strongest approach.",
		focus: "Sharpen your reading strategy",
		subject: "Reading · Targeted strategy",
		steps: [
			"Set your ACT target",
			"Find your section focus",
			"Practice with purpose",
			"Review your approach",
			"Plan your next session"
		],
		icon: BookOpen
	},
	College: {
		title: "Make your next chapter yours.",
		focus: "Build a balanced college list",
		subject: "College planning · Find your fit",
		steps: [
			"Define what matters to you",
			"Learn what makes a good fit",
			"Research your shortlist",
			"Bring your findings back",
			"Choose your next move"
		],
		icon: GraduationCap
	}
};
var CAMERA = [
	{
		p: 0,
		rx: 48,
		ry: 0,
		rz: -27,
		dz: 0,
		ox: 50,
		oy: 50,
		tx: 0,
		ty: 0,
		sc: 1
	},
	{
		p: .3,
		rx: 41,
		ry: 7,
		rz: -21,
		dz: 45,
		ox: 36,
		oy: 55,
		tx: -24,
		ty: -14,
		sc: 1.03
	},
	{
		p: .64,
		rx: 35,
		ry: 12,
		rz: -15,
		dz: 85,
		ox: 63,
		oy: 60,
		tx: -14,
		ty: -24,
		sc: 1.05
	},
	{
		p: 1,
		rx: 30,
		ry: 9,
		rz: -8,
		dz: 112,
		ox: 71,
		oy: 66,
		tx: 4,
		ty: -12,
		sc: 1.04
	}
];
var CAMERA_VARS = [
	[
		"--cam-x",
		"rx",
		"deg"
	],
	[
		"--cam-y",
		"ry",
		"deg"
	],
	[
		"--cam-z",
		"rz",
		"deg"
	],
	[
		"--cam-dolly",
		"dz",
		"px"
	],
	[
		"--cam-origin-x",
		"ox",
		"%"
	],
	[
		"--cam-origin-y",
		"oy",
		"%"
	]
];
var PANELS = [
	{
		enter: [0, 0],
		exit: [.11, .23]
	},
	{
		enter: [.19, .31],
		exit: [.53, .63]
	},
	{
		enter: [.61, .73],
		exit: [2, 3]
	}
];
var STEP_STOPS = [
	[.17, 2],
	[.33, 0],
	[.49, 1],
	[.65, 2],
	[.81, 3],
	[2, 4]
];
var clamp = (value) => value < 0 ? 0 : value > 1 ? 1 : value;
var smooth = (value) => value * value * (3 - 2 * value);
var cameraAt = (progress) => {
	let index = 1;
	while (index < CAMERA.length - 1 && progress > CAMERA[index].p) index += 1;
	const from = CAMERA[index - 1], to = CAMERA[index];
	const eased = smooth(clamp((progress - from.p) / (to.p - from.p)));
	const frame = {};
	for (const key in to) frame[key] = from[key] + (to[key] - from[key]) * eased;
	return frame;
};
function HomeHero({ loggedIn }) {
	const [track, setTrack] = useState("SAT");
	const [activeStep, setActiveStep] = useState(2);
	const sceneRef = useRef(null);
	const heroRef = useRef(null);
	const storyRef = useRef(null);
	const visualRef = useRef(null);
	const progressRef = useRef(null);
	const panelsRef = useRef([]);
	const [chapter, setChapter] = useState(0);
	useEffect(() => {
		const story = storyRef.current;
		const hero = heroRef.current;
		const sculpture = sceneRef.current;
		const visual = visualRef.current;
		const enabled = window.matchMedia("(prefers-reduced-motion: no-preference) and (min-height: 650px)");
		const route = sculpture.querySelector(".path-route-active");
		const parallax = [
			[
				".home-hero-grid",
				0,
				-70
			],
			[
				".home-hero-halo",
				54,
				-46
			],
			[
				".home-hero-orbit--outer",
				-34,
				26
			],
			[
				".hero-left-art",
				-46,
				-20
			]
		].map(([selector, x, y]) => [
			hero.querySelector(selector),
			x,
			y
		]);
		const prompt = hero.querySelector(".hero-scroll-prompt");
		let frame = 0, range = 1, mobile = false;
		let lastChapter = -1, lastStep = -1;
		const measure = () => {
			range = Math.max(1, story.offsetHeight - hero.offsetHeight);
			mobile = window.innerWidth <= 900;
		};
		const render = () => {
			frame = 0;
			if (!enabled.matches) {
				panelsRef.current.forEach((panel) => {
					panel.style.opacity = "";
					panel.style.transform = "";
				});
				CAMERA_VARS.forEach(([name]) => sculpture.style.removeProperty(name));
				parallax.forEach(([node]) => {
					if (node) node.style.translate = "";
				});
				if (prompt) prompt.style.opacity = "";
				visual.style.transform = "";
				story.dataset.scroll = "static";
				setChapter(-1);
				return;
			}
			story.dataset.scroll = "active";
			const progress = clamp(-story.getBoundingClientRect().top / range);
			const current = progress < .17 ? 0 : progress < .58 ? 1 : 2;
			if (current !== lastChapter) {
				lastChapter = current;
				setChapter(current);
			}
			const step = STEP_STOPS.find(([edge]) => progress < edge)[1];
			if (step !== lastStep) {
				lastStep = step;
				setActiveStep(step);
			}
			panelsRef.current.forEach((panel, index) => {
				if (!panel) return;
				const { enter, exit } = PANELS[index];
				const arriving = enter[1] > enter[0] ? clamp((progress - enter[0]) / (enter[1] - enter[0])) : 1;
				const leaving = clamp((progress - exit[0]) / (exit[1] - exit[0]));
				panel.style.opacity = smooth(arriving) * (1 - smooth(leaving));
				panel.style.transform = `translate3d(0, ${(1 - arriving) * 46 - leaving * 54}px, 0) scale(${1 - (1 - arriving) * .045 - leaving * .035})`;
			});
			const camera = cameraAt(progress);
			const damp = mobile ? .55 : 1;
			const shot = (key) => CAMERA[0][key] + (camera[key] - CAMERA[0][key]) * damp;
			CAMERA_VARS.forEach(([name, key, unit]) => sculpture.style.setProperty(name, `${shot(key).toFixed(2)}${unit}`));
			visual.style.transform = `translate3d(${mobile ? 0 : shot("tx").toFixed(2)}px, ${shot("ty").toFixed(2)}px, 0) scale(${shot("sc").toFixed(4)})`;
			parallax.forEach(([node, x, y]) => {
				if (node) node.style.translate = `${(mobile ? 0 : x) * progress}px ${y * progress}px`;
			});
			if (prompt) prompt.style.opacity = String(1 - clamp(progress / .07));
			progressRef.current.style.transform = `scaleX(${progress})`;
			route.style.strokeDashoffset = String(100 - clamp((progress - .05) / .8) * 100);
		};
		const schedule = () => {
			if (!frame) frame = requestAnimationFrame(render);
		};
		const remeasure = () => {
			measure();
			schedule();
		};
		window.addEventListener("scroll", schedule, { passive: true });
		window.addEventListener("resize", remeasure);
		enabled.addEventListener("change", remeasure);
		measure();
		render();
		return () => {
			cancelAnimationFrame(frame);
			window.removeEventListener("scroll", schedule);
			window.removeEventListener("resize", remeasure);
			enabled.removeEventListener("change", remeasure);
		};
	}, []);
	const goToChapter = (index) => {
		const story = storyRef.current;
		const range = story.offsetHeight - heroRef.current.offsetHeight;
		const top = window.scrollY + story.getBoundingClientRect().top + range * [
			0,
			.4,
			.8
		][index];
		window.scrollTo({
			top,
			behavior: "smooth"
		});
	};
	useEffect(() => {
		const hero = heroRef.current;
		let visible = true;
		const update = () => {
			hero.dataset.motion = visible && !document.hidden ? "running" : "paused";
		};
		const observer = new IntersectionObserver(([entry]) => {
			visible = entry.isIntersecting;
			update();
		});
		observer.observe(hero);
		document.addEventListener("visibilitychange", update);
		update();
		return () => {
			observer.disconnect();
			document.removeEventListener("visibilitychange", update);
		};
	}, []);
	useEffect(() => {
		const scene = sceneRef.current;
		const motion = window.matchMedia("(prefers-reduced-motion: no-preference) and (pointer: fine) and (min-width: 901px)");
		let frame = 0;
		let x = 0, y = 0, vx = 0, vy = 0, targetX = 0, targetY = 0, last = 0;
		const tick = (now) => {
			const dt = Math.min((now - (last || now - 16)) / 1e3, .032);
			last = now;
			vx += ((targetX - x) * 100 - vx * 18) * dt;
			vy += ((targetY - y) * 100 - vy * 18) * dt;
			x += vx * dt;
			y += vy * dt;
			scene.style.rotate = `${-y} ${x} 0 ${Math.hypot(x, y)}deg`;
			if (Math.abs(targetX - x) + Math.abs(targetY - y) + Math.abs(vx) + Math.abs(vy) > .01) frame = requestAnimationFrame(tick);
			else {
				frame = 0;
				last = 0;
			}
		};
		const start = () => {
			if (!frame) frame = requestAnimationFrame(tick);
		};
		const move = (event) => {
			if (!motion.matches || event.pointerType === "touch") return;
			const box = scene.parentElement.getBoundingClientRect();
			targetX = ((event.clientX - box.left) / box.width - .5) * 10;
			targetY = ((event.clientY - box.top) / box.height - .5) * 8;
			start();
		};
		const reset = () => {
			targetX = 0;
			targetY = 0;
			start();
		};
		const preferenceChanged = () => {
			cancelAnimationFrame(frame);
			frame = 0;
			x = y = vx = vy = targetX = targetY = last = 0;
			scene.style.rotate = "";
		};
		const parent = scene.parentElement;
		parent.addEventListener("pointermove", move);
		parent.addEventListener("pointerleave", reset);
		motion.addEventListener("change", preferenceChanged);
		return () => {
			cancelAnimationFrame(frame);
			parent.removeEventListener("pointermove", move);
			parent.removeEventListener("pointerleave", reset);
			motion.removeEventListener("change", preferenceChanged);
		};
	}, []);
	const preview = previews[track];
	const Icon = preview.icon;
	return /* @__PURE__ */ jsx("div", {
		className: "hero-scroll-story",
		ref: storyRef,
		children: /* @__PURE__ */ jsxs("section", {
			className: "home-hero",
			ref: heroRef,
			"aria-labelledby": "home-hero-title",
			children: [
				/* @__PURE__ */ jsxs("div", {
					className: "home-hero-atmosphere",
					"aria-hidden": "true",
					children: [
						/* @__PURE__ */ jsx("div", { className: "home-hero-grid" }),
						/* @__PURE__ */ jsx("div", { className: "home-hero-halo" }),
						/* @__PURE__ */ jsx("div", { className: "home-hero-orbit home-hero-orbit--outer" }),
						/* @__PURE__ */ jsx("div", { className: "home-hero-orbit home-hero-orbit--inner" }),
						/* @__PURE__ */ jsx("span", { className: "home-hero-star home-hero-star--one" }),
						/* @__PURE__ */ jsx("span", { className: "home-hero-star home-hero-star--two" }),
						/* @__PURE__ */ jsx("span", { className: "home-hero-star home-hero-star--three" })
					]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "hero-story-copy-stack",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "hero-left-art",
							"aria-hidden": "true",
							children: [
								/* @__PURE__ */ jsx("div", { className: "hero-left-disc" }),
								/* @__PURE__ */ jsx("div", { className: "hero-left-arc" }),
								/* @__PURE__ */ jsx("span", {
									className: "hero-coordinate hero-coordinate--one",
									children: "YOUR GOAL"
								}),
								/* @__PURE__ */ jsx("span", {
									className: "hero-coordinate hero-coordinate--two",
									children: "YOUR PACE"
								}),
								/* @__PURE__ */ jsxs("svg", {
									viewBox: "0 0 550 400",
									children: [
										/* @__PURE__ */ jsx("path", { d: "M-40 330 C70 330 25 110 130 110 S245 300 345 225 S430 25 570 65" }),
										/* @__PURE__ */ jsx("circle", {
											cx: "130",
											cy: "110",
											r: "5"
										}),
										/* @__PURE__ */ jsx("circle", {
											cx: "345",
											cy: "225",
											r: "5"
										})
									]
								})
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "home-hero-copy hero-story-panel",
							ref: (node) => {
								panelsRef.current[0] = node;
							},
							"aria-hidden": chapter !== 0 && chapter !== -1,
							inert: chapter !== 0 && chapter !== -1,
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "home-hero-eyebrow",
									children: [/* @__PURE__ */ jsx("span", {}), " SMALL STEPS. BIG POSSIBILITIES."]
								}),
								/* @__PURE__ */ jsxs("h1", {
									id: "home-hero-title",
									"aria-label": "MENTICS",
									children: ["MENTICS", /* @__PURE__ */ jsx("span", {
										className: "wordmark-sweep",
										"aria-hidden": "true",
										children: "MENTICS"
									})]
								}),
								/* @__PURE__ */ jsxs("p", { children: [
									"From your next test to your next chapter.",
									/* @__PURE__ */ jsx("br", { className: "home-hero-break" }),
									" Personalized SAT, ACT, and college planning that turns ",
									/* @__PURE__ */ jsx("strong", { children: "“where do I start?”" }),
									" into ",
									/* @__PURE__ */ jsx("strong", { children: "“I’ve got this.”" })
								] }),
								/* @__PURE__ */ jsxs("div", {
									className: "home-hero-actions",
									children: [/* @__PURE__ */ jsxs("a", {
										className: "button home-hero-primary",
										href: loggedIn ? "/dashboard" : "/signup",
										children: [
											loggedIn ? "Continue your path" : "Find my starting point",
											" ",
											/* @__PURE__ */ jsx(ArrowRight, { size: 18 })
										]
									}), /* @__PURE__ */ jsxs("a", {
										className: "home-hero-secondary",
										href: "#how-it-works",
										children: ["See how it works ", /* @__PURE__ */ jsx(ArrowRight, { size: 16 })]
									})]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "home-hero-assurance",
									children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Check, { size: 14 }), " Free to get started"] }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Check, { size: 14 }), " Built around you"] })]
								})
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "hero-story-panel hero-story-panel--chapter",
							ref: (node) => {
								panelsRef.current[1] = node;
							},
							"aria-hidden": chapter !== 1 && chapter !== -1,
							inert: chapter !== 1 && chapter !== -1,
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "home-hero-eyebrow",
									children: [/* @__PURE__ */ jsx("span", {}), " 01 / FIND YOUR SIGNAL"]
								}),
								/* @__PURE__ */ jsxs("h2", { children: [
									"It starts",
									/* @__PURE__ */ jsx("br", {}),
									"with ",
									/* @__PURE__ */ jsx("em", { children: "you." })
								] }),
								/* @__PURE__ */ jsx("p", { children: "Your goals. Your starting point. The things that feel hard right now. Mentics turns that context into a direction." }),
								/* @__PURE__ */ jsxs("div", {
									className: "story-context",
									children: [
										/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Target, { size: 16 }), " Your target"] }),
										/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(BookOpen, { size: 16 }), " Your strengths"] }),
										/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Sparkles, { size: 16 }), " Your next opportunity"] })
									]
								})
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "hero-story-panel hero-story-panel--chapter",
							ref: (node) => {
								panelsRef.current[2] = node;
							},
							"aria-hidden": chapter !== 2 && chapter !== -1,
							inert: chapter !== 2 && chapter !== -1,
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "home-hero-eyebrow",
									children: [/* @__PURE__ */ jsx("span", {}), " 02 / TURN CLARITY INTO ACTION"]
								}),
								/* @__PURE__ */ jsxs("h2", { children: [
									"One move.",
									/* @__PURE__ */ jsx("br", {}),
									/* @__PURE__ */ jsx("em", { children: "Real momentum." })
								] }),
								/* @__PURE__ */ jsx("p", { children: "Five focused steps. One clear place to begin. Learn, practice, and bring back the result. Your next path gets smarter with you." }),
								/* @__PURE__ */ jsxs("a", {
									className: "button home-hero-primary",
									href: loggedIn ? "/dashboard" : "/signup",
									children: [
										loggedIn ? "Continue your path" : "Build my free path",
										" ",
										/* @__PURE__ */ jsx(ArrowRight, { size: 18 })
									]
								}),
								/* @__PURE__ */ jsxs("a", {
									className: "story-continue",
									href: "#how-it-works",
									children: ["Keep going. See the method. ", /* @__PURE__ */ jsx(ArrowRight, { size: 16 })]
								})
							]
						})
					]
				}),
				/* @__PURE__ */ jsx("div", {
					className: "hero-story-visual",
					ref: visualRef,
					children: /* @__PURE__ */ jsxs("div", {
						className: "home-hero-demo",
						children: [
							/* @__PURE__ */ jsx("div", {
								className: "home-hero-track",
								role: "group",
								"aria-label": "Choose a sample study path",
								children: Object.keys(previews).map((name) => /* @__PURE__ */ jsx("button", {
									type: "button",
									"aria-pressed": track === name,
									"aria-controls": "home-path-preview",
									onClick: () => {
										setTrack(name);
										setActiveStep(2);
									},
									children: name
								}, name))
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "home-hero-stage",
								children: [/* @__PURE__ */ jsxs("div", {
									className: "path-scene",
									id: "home-path-preview",
									"aria-live": "polite",
									"aria-atomic": "true",
									children: [
										/* @__PURE__ */ jsxs("div", {
											className: "path-scene-heading",
											children: [/* @__PURE__ */ jsxs("span", { children: [
												/* @__PURE__ */ jsx(Sparkles, { size: 14 }),
												" ",
												track,
												" · SAMPLE PATH"
											] }), /* @__PURE__ */ jsx("h2", { children: preview.title })]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "path-sculpture",
											ref: sceneRef,
											children: [
												/* @__PURE__ */ jsx("div", {
													className: "path-plinth path-plinth--bottom",
													"aria-hidden": "true"
												}),
												/* @__PURE__ */ jsx("div", {
													className: "path-plinth path-plinth--middle",
													"aria-hidden": "true"
												}),
												/* @__PURE__ */ jsxs("div", {
													className: "path-plane",
													children: [
														/* @__PURE__ */ jsx("div", {
															className: "path-plane-grid",
															"aria-hidden": "true"
														}),
														/* @__PURE__ */ jsxs("svg", {
															className: "path-sculpture-route",
															viewBox: "0 0 500 440",
															"aria-hidden": "true",
															children: [
																/* @__PURE__ */ jsx("path", {
																	className: "path-route-shadow",
																	d: "M100 88 C100 15 350 25 350 119 S225 132 225 220 S375 230 375 317 S125 410 125 361"
																}),
																/* @__PURE__ */ jsx("path", {
																	className: "path-route-base",
																	d: "M100 88 C100 15 350 25 350 119 S225 132 225 220 S375 230 375 317 S125 410 125 361"
																}),
																/* @__PURE__ */ jsx("path", {
																	className: "path-route-active",
																	pathLength: "100",
																	strokeDasharray: "100",
																	d: "M100 88 C100 15 350 25 350 119 S225 132 225 220 S375 230 375 317 S125 410 125 361"
																})
															]
														}),
														/* @__PURE__ */ jsx("ol", {
															className: "path-milestones",
															children: preview.steps.map((step, index) => /* @__PURE__ */ jsxs("li", {
																className: `path-milestone path-milestone--${index} ${index === activeStep ? "is-active" : ""}`,
																children: [
																	/* @__PURE__ */ jsx("span", {
																		className: "path-pedestal",
																		"aria-hidden": "true"
																	}),
																	/* @__PURE__ */ jsx("button", {
																		type: "button",
																		className: "path-token",
																		"aria-pressed": activeStep === index,
																		"aria-label": `Explore step ${index + 1}: ${step}`,
																		onClick: () => setActiveStep(index),
																		children: index < 2 ? /* @__PURE__ */ jsx(Check, {}) : index === 2 ? /* @__PURE__ */ jsx(Icon, {}) : index === 4 ? /* @__PURE__ */ jsx(Flag, {}) : /* @__PURE__ */ jsx(LockKeyhole, {})
																	}),
																	/* @__PURE__ */ jsxs("span", {
																		className: "path-milestone-label",
																		children: [/* @__PURE__ */ jsxs("small", { children: [
																			"0",
																			index + 1,
																			index === activeStep ? " / EXPLORING" : ""
																		] }), step]
																	})
																]
															}, index))
														}),
														/* @__PURE__ */ jsx("span", {
															className: "path-plane-signature",
															"aria-hidden": "true",
															children: "MENTICS / YOUR NEXT CHAPTER"
														})
													]
												})
											]
										}),
										/* @__PURE__ */ jsxs("div", {
											className: "path-orbit-badge",
											"aria-hidden": "true",
											children: [/* @__PURE__ */ jsx(Sparkles, { size: 18 }), /* @__PURE__ */ jsxs("span", { children: ["Made for your", /* @__PURE__ */ jsx("strong", { children: "next breakthrough." })] })]
										})
									]
								}), /* @__PURE__ */ jsxs("div", {
									className: "home-focus-card",
									children: [
										/* @__PURE__ */ jsx("span", {
											className: "home-focus-icon",
											children: /* @__PURE__ */ jsx(Icon, { size: 21 })
										}),
										/* @__PURE__ */ jsxs("div", { children: [
											/* @__PURE__ */ jsxs("small", { children: [
												"STEP ",
												String(activeStep + 1).padStart(2, "0"),
												" / YOUR NEXT MOVE"
											] }),
											/* @__PURE__ */ jsx("strong", { children: activeStep === 2 ? preview.focus : preview.steps[activeStep] }),
											/* @__PURE__ */ jsx("span", { children: preview.subject })
										] }),
										/* @__PURE__ */ jsx("button", {
											type: "button",
											className: "home-focus-spark",
											"aria-label": "Explore the next sample step",
											onClick: () => setActiveStep((step) => (step + 1) % 5),
											children: /* @__PURE__ */ jsx(ArrowRight, { size: 18 })
										})
									]
								})]
							}),
							/* @__PURE__ */ jsxs("p", {
								className: "home-hero-caption",
								children: [/* @__PURE__ */ jsx("span", {}), " Pick a milestone. See where it takes you."]
							})
						]
					})
				}),
				/* @__PURE__ */ jsxs("nav", {
					className: "hero-story-nav",
					"aria-label": "Hero story chapters",
					children: [
						/* @__PURE__ */ jsx("div", {
							className: "hero-story-nav-track",
							children: /* @__PURE__ */ jsx("i", { ref: progressRef })
						}),
						[
							"Your ambition",
							"Your signal",
							"Your next move"
						].map((label, index) => /* @__PURE__ */ jsxs("button", {
							type: "button",
							"aria-current": chapter === index ? "step" : void 0,
							onClick: () => goToChapter(index),
							children: [/* @__PURE__ */ jsxs("span", { children: ["0", index + 1] }), label]
						}, label)),
						/* @__PURE__ */ jsxs("a", {
							href: "#how-it-works",
							children: ["Skip to the method ", /* @__PURE__ */ jsx(ArrowRight, { size: 14 })]
						})
					]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "hero-scroll-prompt",
					"aria-hidden": "true",
					children: [/* @__PURE__ */ jsx("span", {}), " SCROLL TO FIND YOUR PATH"]
				})
			]
		})
	});
}
//#endregion
//#region frontend/src/app-runtime.jsx
var ArenaRouteBoundary = class extends Component {
	state = { failed: false };
	static getDerivedStateFromError() {
		return { failed: true };
	}
	render() {
		if (!this.state.failed) return this.props.children;
		return /* @__PURE__ */ jsx(AppShell, {
			name: boot.data.name,
			children: /* @__PURE__ */ jsxs("main", {
				className: "app-main",
				role: "alert",
				children: [
					/* @__PURE__ */ jsx("h1", { children: "The Arena could not open." }),
					/* @__PURE__ */ jsx("p", { children: "Reload to reconnect. Your saved loadout and progress are kept." }),
					/* @__PURE__ */ jsx("button", {
						className: "button button--primary",
						onClick: () => window.location.reload(),
						children: "Reload Arena"
					})
				]
			})
		});
	}
};
var noopSubscribe = () => () => {};
function useClientOnly(value, fallback = "") {
	return useSyncExternalStore(noopSubscribe, () => value, () => fallback);
}
function CsrfField() {
	const token = useClientOnly(boot.data.csrfToken || "");
	return /* @__PURE__ */ jsx("input", {
		type: "hidden",
		name: "_csrf_token",
		value: token
	});
}
function Brand({ inverse = false }) {
	return /* @__PURE__ */ jsx("a", {
		className: `brand ${inverse ? "brand--inverse" : ""}`,
		href: "/",
		"aria-label": "Mentics home",
		children: "MENTICS"
	});
}
var navItems = [
	[
		"/dashboard",
		LayoutDashboard,
		"Home"
	],
	[
		"/dashboard/test-path-view",
		Target,
		"Test path"
	],
	[
		"/dashboard/college-path-view",
		GraduationCap,
		"College path"
	],
	[
		"/dashboard/stats",
		BarChart3,
		"Stats"
	],
	[
		"/dashboard/tracker",
		LineChart,
		"Tracker"
	],
	[
		"/battles",
		Swords,
		"SAT Battles"
	],
	[
		"/forum",
		MessageCircle,
		"Community"
	],
	[
		"/points",
		Award,
		"Points & achievements"
	],
	[
		"/account",
		Settings,
		"Settings"
	]
];
function Starfield({ warp = false, tone = "violet" }) {
	const ref = useRef(null);
	useEffect(() => {
		const canvas = ref.current;
		const ctx = canvas?.getContext("2d");
		if (!ctx) return;
		const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
		let frame;
		let width = 0;
		let height = 0;
		let points = [];
		let active = !document.hidden;
		const color = tone === "indigo" ? [
			79,
			70,
			229
		] : [
			124,
			58,
			237
		];
		const resize = () => {
			const ratio = Math.min(window.devicePixelRatio || 1, 2);
			width = canvas.clientWidth;
			height = canvas.clientHeight;
			canvas.width = width * ratio;
			canvas.height = height * ratio;
			ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
			const count = warp ? Math.min(720, Math.floor(width * height / 1200)) : Math.min(120, Math.floor(width * height / 1e4));
			points = Array.from({ length: count }, () => warp ? {
				x: (Math.random() - .5) * width,
				y: (Math.random() - .5) * height,
				z: Math.random() * .9 + .1
			} : {
				x: Math.random() * width,
				y: Math.random() * height,
				r: Math.random() * 1.4 + .3,
				v: Math.random() * .12 + .03,
				a: Math.random() * .55 + .15
			});
		};
		const draw = () => {
			if (!active) {
				frame = void 0;
				return;
			}
			ctx.clearRect(0, 0, width, height);
			if (warp) {
				const cx = width / 2, cy = height / 2;
				points.forEach((p) => {
					p.z -= .012;
					if (p.z < .02) {
						p.x = (Math.random() - .5) * width;
						p.y = (Math.random() - .5) * height;
						p.z = 1;
					}
					const scale = 1 / p.z;
					const x = cx + p.x * scale * .25;
					const y = cy + p.y * scale * .25;
					const tail = 8 + (1 - p.z) * 36;
					ctx.beginPath();
					ctx.moveTo(x, y);
					ctx.lineTo(cx + (x - cx) * (1 + tail / Math.max(width, height)), cy + (y - cy) * (1 + tail / Math.max(width, height)));
					ctx.strokeStyle = `rgba(${color.join(",")},${Math.min(1, 1 - p.z + .2)})`;
					ctx.lineWidth = Math.max(.5, (1 - p.z) * 2.4);
					ctx.stroke();
				});
			} else points.forEach((p) => {
				p.y -= p.v;
				if (p.y < 0) p.y = height;
				ctx.beginPath();
				ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
				ctx.fillStyle = `rgba(${color.join(",")},${p.a})`;
				ctx.fill();
			});
			if (!reduced) frame = requestAnimationFrame(draw);
		};
		const setActive = () => {
			active = !document.hidden;
			if (active && !frame && !reduced) frame = requestAnimationFrame(draw);
		};
		resize();
		draw();
		window.addEventListener("resize", resize);
		document.addEventListener("visibilitychange", setActive);
		const observer = new IntersectionObserver(([entry]) => {
			active = entry.isIntersecting && !document.hidden;
			if (active && !frame && !reduced) frame = requestAnimationFrame(draw);
			if (!active) {
				cancelAnimationFrame(frame);
				frame = void 0;
			}
		}, { threshold: 0 });
		observer.observe(canvas);
		return () => {
			cancelAnimationFrame(frame);
			observer.disconnect();
			window.removeEventListener("resize", resize);
			document.removeEventListener("visibilitychange", setActive);
		};
	}, [warp, tone]);
	return /* @__PURE__ */ jsx("canvas", {
		ref,
		className: warp ? "warp-field" : "star-field",
		"aria-hidden": "true"
	});
}
function AppShell({ children, name }) {
	const [menu, setMenu] = useState(false);
	const [navWarp, setNavWarp] = useState(null);
	const current = typeof window === "undefined" ? "" : window.location.pathname;
	const active = (href) => current === href || href === "/dashboard/test-path-view" && current.startsWith("/dashboard/test-path") || href === "/dashboard/college-path-view" && current.startsWith("/dashboard/college-path") || href !== "/dashboard" && current.startsWith(`${href}/`);
	const travel = (event, href, label) => {
		if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || current === href) return;
		if (!(href === "/dashboard/test-path-view" || href === "/dashboard/college-path-view")) return;
		event.preventDefault();
		setMenu(false);
		setNavWarp({
			href,
			label
		});
		const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
		window.setTimeout(() => {
			window.location.href = href;
		}, reduced ? 60 : 420);
	};
	return /* @__PURE__ */ jsxs("div", {
		className: "app-shell app-shell--tabs",
		children: [
			/* @__PURE__ */ jsx(Starfield, {}),
			/* @__PURE__ */ jsxs("header", {
				className: "product-nav",
				children: [
					/* @__PURE__ */ jsx(Brand, {}),
					/* @__PURE__ */ jsx("nav", {
						id: "mobile-product-navigation",
						className: menu ? "open" : "",
						"aria-label": "Product navigation",
						children: navItems.map(([href, Icon, label]) => /* @__PURE__ */ jsxs("a", {
							className: active(href) ? "active" : "",
							href,
							"aria-current": active(href) ? "page" : void 0,
							title: label,
							onClick: (event) => travel(event, href, label),
							children: [/* @__PURE__ */ jsx(Icon, { size: 17 }), /* @__PURE__ */ jsx("span", { children: label })]
						}, href))
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "product-account",
						children: [/* @__PURE__ */ jsxs("a", {
							href: "/account",
							onClick: (event) => travel(event, "/account", "Settings"),
							children: [/* @__PURE__ */ jsx("i", { children: (name || "M").slice(0, 1).toUpperCase() }), /* @__PURE__ */ jsx("span", { children: name || "Mentics student" })]
						}), /* @__PURE__ */ jsxs("form", {
							className: "product-logout",
							method: "POST",
							action: "/logout",
							children: [/* @__PURE__ */ jsx(CsrfField, {}), /* @__PURE__ */ jsx("button", {
								type: "submit",
								"aria-label": "Log out",
								children: /* @__PURE__ */ jsx(LogOut, { size: 17 })
							})]
						})]
					}),
					/* @__PURE__ */ jsx("button", {
						className: "product-menu",
						type: "button",
						onClick: () => setMenu(!menu),
						"aria-label": menu ? "Close navigation" : "Open navigation",
						"aria-controls": "mobile-product-navigation",
						"aria-expanded": menu,
						children: menu ? /* @__PURE__ */ jsx(X, {}) : /* @__PURE__ */ jsx(Menu, {})
					})
				]
			}),
			menu && /* @__PURE__ */ jsx("button", {
				className: "menu-scrim",
				onClick: () => setMenu(false),
				"aria-label": "Close navigation"
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "app-stage",
				children: [[
					"test-builder",
					"college-builder",
					"edit-stats"
				].includes(boot.page) && boot.data.error && /* @__PURE__ */ jsx("div", {
					className: "shell-error",
					role: "alert",
					children: boot.data.error
				}), children]
			}),
			navWarp && createPortal(/* @__PURE__ */ jsxs("div", {
				className: "warp-overlay warp-overlay--nav",
				"aria-live": "polite",
				children: [/* @__PURE__ */ jsx(Starfield, {
					warp: true,
					tone: "violet"
				}), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(Brand, { inverse: true }), /* @__PURE__ */ jsxs("p", { children: ["Opening ", navWarp.label] })] })]
			}), document.body)
		]
	});
}
async function api(url, options = {}) {
	const method = String(options.method || "GET").toUpperCase();
	const token = boot.data.csrfToken || "";
	const csrfHeader = ![
		"GET",
		"HEAD",
		"OPTIONS"
	].includes(method) && token ? { "X-CSRF-Token": token } : {};
	const response = await fetch(url, {
		headers: {
			"Content-Type": "application/json",
			...csrfHeader,
			...options.headers || {}
		},
		...options
	});
	const data = await response.json().catch(() => ({}));
	if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
	return data;
}
//#endregion
//#region frontend/src/App.jsx
var BattleArena = lazy(() => import("./assets/arena-page-tKe-sm9N.js").then((n) => n.t));
var productPages = {
	"ai-sat-prep": {
		eyebrow: "PERSONALIZED AI SAT PREP",
		title: "SAT prep that gets smarter after every answer.",
		intro: "Mentics turns your real scores, per-skill mastery, and mistake patterns into a focused five-step SAT study path. You always know what to do next—and why it matters.",
		primary: "Build my SAT path",
		signal: [
			["5", "focused steps"],
			["2", "SAT sections"],
			["1", "adaptive system"]
		],
		heroCard: {
			label: "YOUR NEXT PATH",
			title: "Strengthen transitions",
			detail: "Your recent answers show this is the highest-impact skill to work on next.",
			steps: [
				"Learn the decision rule",
				"Compare strong and weak transitions",
				"Complete a focused practice set",
				"Review your mistake pattern",
				"Prove mastery in a checkpoint"
			]
		},
		methodTitle: "AI should use evidence, not guesswork.",
		methodIntro: "The first path starts with what you tell Mentics. After that, the planner reads what you actually did.",
		method: [
			[
				"01",
				"Start with your baseline",
				"Add your SAT score, target, test date, schedule, and the skills that feel weakest."
			],
			[
				"02",
				"Learn through focused work",
				"Short lessons, original SAT-style questions, explanations, and checkpoints turn a broad goal into finishable sessions."
			],
			[
				"03",
				"Adapt from real performance",
				"Measured mastery and your mistake bank shape the next unit, so repeated work gives way to the skills that need it most."
			]
		],
		featureTitle: "One study loop, fully connected.",
		features: [
			[
				Brain,
				"Adaptive planning",
				"Each five-step unit is built around current evidence instead of a fixed calendar."
			],
			[
				Target,
				"Skill-level focus",
				"Reading and Writing and Math performance are tracked by the underlying skill, not only a total score."
			],
			[
				BookOpen,
				"Lessons before testing",
				"Learn the idea, see it applied, practice it, and then prove that it stuck."
			],
			[
				LineChart,
				"Progress you can explain",
				"Scores, accuracy, mastery, completed paths, streaks, and mistakes live in one view."
			]
		],
		detailTitle: "What makes Mentics different from a generic AI tutor?",
		detailCopy: "A blank chatbot waits for you to know what to ask. Mentics keeps the learning loop moving. The path assigns a useful next lesson or task, the work creates evidence, and the next path uses that evidence. You can still ask the Mentics Guide for help, but the product does not depend on prompts to create structure.",
		faq: [
			["Does Mentics generate a new plan as I improve?", "Yes. New paths can use completed work, measured skill mastery, logged scores, and mistake patterns so the focus changes with you."],
			["Does the AI replace official SAT material?", "No. Mentics provides original SAT-style learning and practice. Students should also use official materials and guidance from College Board."],
			["Can I use Mentics before I have a score?", "Yes. Your first unit can begin from your goals and self-reported weaknesses, then become more precise as answer data accumulates."]
		]
	},
	"sat-prep": {
		eyebrow: "SAT PREP, WITHOUT THE CLUTTER",
		title: "Prepare for the SAT with a path you can actually finish.",
		intro: "Study SAT Math and Reading and Writing through focused lessons, original SAT-style practice, skill tracking, and a plan that updates when your results change.",
		primary: "Start SAT prep",
		signal: [
			["RW", "skill mastery"],
			["MATH", "targeted practice"],
			["LIVE", "timed battles"]
		],
		heroCard: {
			label: "SAT STUDY SESSION",
			title: "A complete learning loop",
			detail: "Move from strategy to practice without losing the reason behind the work.",
			steps: [
				"Learn one tested concept",
				"Work through an example",
				"Answer a focused set",
				"Review every miss",
				"Update your mastery"
			]
		},
		methodTitle: "Train the skill—not just the score.",
		methodIntro: "A total score shows where you landed. Mentics helps reveal what caused it.",
		method: [
			[
				"01",
				"Set the target",
				"Choose SAT, add section scores when you have them, set a target, and tell Mentics when you plan to test."
			],
			[
				"02",
				"Work by skill",
				"Build command of algebra, advanced math, grammar, transitions, vocabulary in context, and other SAT-tested skills."
			],
			[
				"03",
				"Practice under pressure",
				"Use checkpoints and optional SAT Battle Arena rounds to test accuracy, pacing, and decision-making."
			]
		],
		featureTitle: "More than a question bank.",
		features: [
			[
				BookOpen,
				"Concept-first lessons",
				"Lessons establish the rule or strategy before asking you to perform under time pressure."
			],
			[
				Zap,
				"Original SAT-style practice",
				"Fresh practice includes the context, blanks, answer choices, and explanations the question requires."
			],
			[
				Swords,
				"SAT Battle Arena",
				"Race through shared five-question sets; question complexity rises with Arena rank."
			],
			[
				BarChart3,
				"Score and mastery tracking",
				"Keep section scores, total history, accuracy, streaks, and skill-level progress connected."
			]
		],
		detailTitle: "How SAT difficulty scales in Mentics",
		detailCopy: "The foundations still use complete SAT-style prompts rather than trivia. Higher difficulty adds denser wording, multi-step reasoning, close distractors, less obvious strategy cues, and tighter pacing. In the Arena, the stronger player’s rank controls a shared set so neither player receives a soft version.",
		faq: [
			["Does Mentics cover both SAT sections?", "Yes. Mentics supports SAT Math and SAT Reading and Writing planning, lessons, practice, and skill tracking."],
			["Are the questions copied from College Board?", "No. Mentics questions are original SAT-style practice and are not official College Board questions."],
			["Can I practice against another student?", "Yes. The SAT Battle Arena offers ranked matchmaking and private bot training across every Arena rank."]
		]
	},
	"act-prep": {
		eyebrow: "PERSONALIZED ACT STUDY PLANNING",
		title: "Turn your ACT goal into the next five useful moves.",
		intro: "Mentics builds a focused ACT prep path from your current score, target, schedule, and weaknesses—then keeps your study plan and progress together.",
		primary: "Build my ACT path",
		signal: [
			["3", "core ACT sections"],
			["5", "steps per path"],
			["1", "clear priority"]
		],
		heroCard: {
			label: "ACT PATH SNAPSHOT",
			title: "Make the plan specific",
			detail: "Your scores and test date help Mentics prioritize the work with the best chance of moving your composite.",
			steps: [
				"Review the weakest section",
				"Learn a targeted strategy",
				"Complete timed practice",
				"Analyze missed questions",
				"Log the result and replan"
			]
		},
		methodTitle: "A study plan should fit your actual ACT profile.",
		methodIntro: "Mentics keeps section-level context visible so a composite score does not hide the work that matters.",
		method: [
			[
				"01",
				"Choose ACT only",
				"The onboarding flow stays relevant to the exam you selected instead of mixing SAT and ACT questions."
			],
			[
				"02",
				"Add useful context",
				"Record your composite, section scores, target, test date, schedule, and the areas where you lose the most points."
			],
			[
				"03",
				"Run focused cycles",
				"Complete one five-step path, log what changed, and generate the next cycle from fresher evidence."
			]
		],
		featureTitle: "A calmer way to organize ACT prep.",
		features: [
			[
				Target,
				"Goal-based paths",
				"Connect every study unit to your target score and available preparation time."
			],
			[
				CalendarDays,
				"Test-date awareness",
				"Keep the plan grounded in the date you are actually working toward."
			],
			[
				BarChart3,
				"Section score context",
				"Track the numbers behind the composite instead of reducing progress to one total."
			],
			[
				MessageCircle,
				"Guidance in context",
				"Ask the Mentics Guide about the path or task you are already working through."
			]
		],
		detailTitle: "ACT planning that changes when your situation does",
		detailCopy: "A study schedule made once can become irrelevant after a new practice test, a missed week, or a changed test date. Mentics keeps paths short on purpose. Five steps are enough to create direction, and the next cycle can respond to the results instead of dragging an outdated plan forward.",
		faq: [
			["Can I select only ACT during onboarding?", "Yes. Selecting ACT keeps the test-prep onboarding focused on ACT goals and scores."],
			["Can I update my ACT scores later?", "Yes. Your score profile can be updated as new results arrive so the dashboard and planning context stay current."],
			["Is Mentics affiliated with ACT, Inc.?", "No. Mentics is an independent platform and is not affiliated with or endorsed by ACT, Inc."]
		]
	},
	"college-planning": {
		eyebrow: "AI COLLEGE PLANNING",
		title: "Learn the strategy. Do the real task. Bring the result back.",
		intro: "Mentics turns college planning into short lessons and concrete application work—from building a balanced list to essays, activities, deadlines, and submission.",
		primary: "Build my college path",
		signal: [
			["LEARN", "the judgement"],
			["DO", "the real work"],
			["REPORT", "what changed"]
		],
		heroCard: {
			label: "COLLEGE PLANNING LOOP",
			title: "From advice to a real deliverable",
			detail: "The AI teaches what good work looks like, assigns something useful, and remembers the result.",
			steps: [
				"Learn the decision framework",
				"Compare weak and strong examples",
				"Complete a real application task",
				"Report the outcome to Mentics",
				"Continue with updated context"
			]
		},
		methodTitle: "College planning is not a multiple-choice quiz.",
		methodIntro: "The work is judgement, writing, research, and follow-through. Mentics is designed around that reality.",
		method: [
			[
				"01",
				"Set the stage",
				"Add your grade, application stage, goals, deadlines, and colleges you are exploring."
			],
			[
				"02",
				"Learn before doing",
				"See the principle and examine stronger and weaker examples before applying it to your own application."
			],
			[
				"03",
				"Complete and report",
				"Do the real task, return with what happened, and let Mentics use that context to choose what comes next."
			]
		],
		featureTitle: "A planning workspace that remembers the work.",
		features: [
			[
				GraduationCap,
				"Stage-aware paths",
				"A senior drafting Common App essays should not receive the same plan as a student just beginning a college list."
			],
			[
				Search,
				"College discovery",
				"Search for colleges during onboarding instead of maintaining an unstructured text list."
			],
			[
				PenLine,
				"Essay guidance",
				"Study structure and examples, then get feedback that protects your voice rather than replacing it."
			],
			[
				Check,
				"Real deliverables",
				"Finish tasks that move an application forward, then report the result so the plan can continue intelligently."
			]
		],
		detailTitle: "What an adaptive college path looks like",
		detailCopy: "A path might teach how to balance a college list, assign research on academic and financial fit, then ask you to record what you found. Later paths can use those reported outcomes. For an application-stage student, the loop can shift to essay openings, activities descriptions, review, and submission readiness.",
		faq: [
			["Will Mentics write my application for me?", "No. Mentics can teach, organize, and give feedback, but your application must remain accurate and authentically yours."],
			["Does Mentics guarantee admission?", "No. Admissions decisions are made by colleges and depend on many factors outside the platform."],
			["Is Mentics endorsed by any college or university?", "No. Mentics is independent and is not affiliated with or endorsed by any college or university."]
		]
	}
};
var productLinks = [
	["/ai-sat-prep", "AI SAT Prep"],
	["/sat-prep", "SAT Prep"],
	["/act-prep", "ACT Prep"],
	["/college-planning", "College Planning"]
];
function ProductPage({ kind }) {
	if (kind !== "college-planning") return /* @__PURE__ */ jsx(ExamLanding, { kind });
	const d = productPages[kind];
	return /* @__PURE__ */ jsxs("div", {
		className: "product-story",
		children: [
			/* @__PURE__ */ jsxs("header", {
				className: "product-story-nav",
				children: [
					/* @__PURE__ */ jsx(Brand, {}),
					/* @__PURE__ */ jsx("nav", {
						"aria-label": "Product navigation",
						children: productLinks.map(([href, label]) => /* @__PURE__ */ jsx("a", {
							href,
							"aria-current": kind === href.slice(1) ? "page" : void 0,
							children: label
						}, href))
					}),
					/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("a", {
						href: "/login",
						children: "Log in"
					}), /* @__PURE__ */ jsxs("a", {
						className: "button button--small button--dark",
						href: "/signup",
						children: ["Start free ", /* @__PURE__ */ jsx(ArrowRight, { size: 15 })]
					})] })
				]
			}),
			/* @__PURE__ */ jsxs("main", { children: [
				/* @__PURE__ */ jsxs("section", {
					className: "product-story-hero",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "product-story-copy",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [
									/* @__PURE__ */ jsx("span", {}),
									" ",
									d.eyebrow
								]
							}),
							/* @__PURE__ */ jsx("h1", { children: d.title }),
							/* @__PURE__ */ jsx("p", { children: d.intro }),
							/* @__PURE__ */ jsxs("div", {
								className: "product-story-actions",
								children: [/* @__PURE__ */ jsxs("a", {
									className: "button button--primary",
									href: "/signup",
									children: [
										d.primary,
										" ",
										/* @__PURE__ */ jsx(ArrowRight, { size: 18 })
									]
								}), /* @__PURE__ */ jsx("a", {
									href: "#how-it-works",
									children: "See how it works"
								})]
							}),
							/* @__PURE__ */ jsx("div", {
								className: "product-story-signals",
								children: d.signal.map(([value, label]) => /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: value }), /* @__PURE__ */ jsx("small", { children: label })] }, label))
							})
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "product-story-card",
						"aria-label": d.heroCard.label,
						children: [
							/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("span", { children: [
								/* @__PURE__ */ jsx(Sparkles, {}),
								" ",
								d.heroCard.label
							] }), /* @__PURE__ */ jsx("i", { children: "MENTICS" })] }),
							/* @__PURE__ */ jsx("h2", { children: d.heroCard.title }),
							/* @__PURE__ */ jsx("p", { children: d.heroCard.detail }),
							/* @__PURE__ */ jsx("ol", { children: d.heroCard.steps.map((step, index) => /* @__PURE__ */ jsxs("li", { children: [
								/* @__PURE__ */ jsx("b", { children: String(index + 1).padStart(2, "0") }),
								/* @__PURE__ */ jsx("span", { children: step }),
								index < 2 ? /* @__PURE__ */ jsx(Check, {}) : /* @__PURE__ */ jsx("i", {})
							] }, step)) })
						]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "product-story-method",
					id: "how-it-works",
					children: [/* @__PURE__ */ jsxs("header", { children: [
						/* @__PURE__ */ jsxs("div", {
							className: "eyebrow",
							children: [/* @__PURE__ */ jsx("span", {}), " HOW IT WORKS"]
						}),
						/* @__PURE__ */ jsx("h2", { children: d.methodTitle }),
						/* @__PURE__ */ jsx("p", { children: d.methodIntro })
					] }), /* @__PURE__ */ jsx("div", { children: d.method.map(([number, title, copy]) => /* @__PURE__ */ jsxs("article", { children: [
						/* @__PURE__ */ jsx("b", { children: number }),
						/* @__PURE__ */ jsx("h3", { children: title }),
						/* @__PURE__ */ jsx("p", { children: copy })
					] }, number)) })]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "product-story-features",
					children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("div", {
						className: "eyebrow eyebrow--light",
						children: [/* @__PURE__ */ jsx("span", {}), " INSIDE MENTICS"]
					}), /* @__PURE__ */ jsx("h2", { children: d.featureTitle })] }), /* @__PURE__ */ jsx("div", { children: d.features.map(([Icon, title, copy]) => /* @__PURE__ */ jsxs("article", { children: [
						/* @__PURE__ */ jsx(Icon, {}),
						/* @__PURE__ */ jsx("h3", { children: title }),
						/* @__PURE__ */ jsx("p", { children: copy })
					] }, title)) })]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "product-story-detail",
					children: [/* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsxs("div", {
							className: "eyebrow",
							children: [/* @__PURE__ */ jsx("span", {}), " BUILT AROUND REAL PROGRESS"]
						}),
						/* @__PURE__ */ jsx("h2", { children: d.detailTitle }),
						/* @__PURE__ */ jsx("p", { children: d.detailCopy }),
						/* @__PURE__ */ jsxs("a", {
							href: "/signup",
							children: ["Create your free path ", /* @__PURE__ */ jsx(ArrowRight, { size: 16 })]
						})
					] }), /* @__PURE__ */ jsxs("aside", { children: [
						/* @__PURE__ */ jsx(Brain, {}),
						/* @__PURE__ */ jsx("small", { children: "THE MENTICS LOOP" }),
						/* @__PURE__ */ jsx("strong", { children: "Context" }),
						/* @__PURE__ */ jsx("i", {}),
						/* @__PURE__ */ jsx("strong", { children: "Focused work" }),
						/* @__PURE__ */ jsx("i", {}),
						/* @__PURE__ */ jsx("strong", { children: "Evidence" }),
						/* @__PURE__ */ jsx("i", {}),
						/* @__PURE__ */ jsx("strong", { children: "Sharper next step" })
					] })]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "product-story-faq",
					children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("div", {
						className: "eyebrow",
						children: [/* @__PURE__ */ jsx("span", {}), " QUESTIONS"]
					}), /* @__PURE__ */ jsx("h2", { children: "Know before you start." })] }), /* @__PURE__ */ jsx("div", { children: d.faq.map(([q, a]) => /* @__PURE__ */ jsxs("details", { children: [/* @__PURE__ */ jsxs("summary", { children: [q, /* @__PURE__ */ jsx(Plus, {})] }), /* @__PURE__ */ jsx("p", { children: a })] }, q)) })]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "product-story-related",
					children: [
						/* @__PURE__ */ jsx("small", { children: "EXPLORE MENTICS" }),
						/* @__PURE__ */ jsx("h2", { children: "One platform for the whole journey." }),
						/* @__PURE__ */ jsx("div", { children: productLinks.filter(([href]) => href !== `/${kind}`).map(([href, label]) => /* @__PURE__ */ jsxs("a", {
							href,
							children: [/* @__PURE__ */ jsx("span", { children: label }), /* @__PURE__ */ jsx(ArrowRight, {})]
						}, href)) })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "product-story-cta",
					children: [
						/* @__PURE__ */ jsx(Brand, { inverse: true }),
						/* @__PURE__ */ jsx("h2", { children: "Make the next move obvious." }),
						/* @__PURE__ */ jsx("p", { children: "Build a focused path from where you are to where you want to go." }),
						/* @__PURE__ */ jsxs("a", {
							className: "button button--light",
							href: "/signup",
							children: ["Get started free ", /* @__PURE__ */ jsx(ArrowRight, {})]
						})
					]
				})
			] }),
			/* @__PURE__ */ jsxs("footer", {
				className: "product-story-footer",
				children: [
					/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(Brand, {}), /* @__PURE__ */ jsx("p", { children: "Personalized test prep and college planning, one focused step at a time." })] }),
					/* @__PURE__ */ jsx("nav", {
						"aria-label": "Product links",
						children: productLinks.map(([href, label]) => /* @__PURE__ */ jsx("a", {
							href,
							children: label
						}, href))
					}),
					/* @__PURE__ */ jsxs("nav", {
						"aria-label": "Legal links",
						children: [
							/* @__PURE__ */ jsx("a", {
								href: "/terms",
								children: "Terms"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "/privacy",
								children: "Privacy"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "mailto:thementicsapp@gmail.com",
								children: "Contact"
							})
						]
					}),
					/* @__PURE__ */ jsx("p", {
						className: "product-story-disclaimer",
						children: "Mentics is independent and is not affiliated with or endorsed by College Board, ACT, Inc., or any college or university. SAT is a registered trademark of College Board. ACT is a registered trademark of ACT, Inc."
					}),
					/* @__PURE__ */ jsx("span", { children: "© 2026 Mentics. All rights reserved." })
				]
			})
		]
	});
}
function ExamLanding({ kind }) {
	const d = productPages[kind];
	const exam = kind === "act-prep" ? "ACT" : "SAT";
	const loggedIn = useClientOnly(boot.data.isLoggedIn, false);
	const destination = loggedIn ? "/dashboard" : "/signup";
	const methodIcons = [
		Target,
		BookOpen,
		BarChart3
	];
	return /* @__PURE__ */ jsxs("div", {
		className: "landing exam-landing",
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "story-progress",
				"aria-hidden": "true"
			}),
			/* @__PURE__ */ jsx(Starfield, {}),
			/* @__PURE__ */ jsxs("header", {
				className: "public-nav",
				children: [
					/* @__PURE__ */ jsx(Brand, {}),
					/* @__PURE__ */ jsxs("nav", {
						"aria-label": "Main navigation",
						children: [
							/* @__PURE__ */ jsx("a", {
								href: "#how-it-works",
								children: "How it works"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "/sat-prep",
								"aria-current": exam === "SAT" ? "page" : void 0,
								children: "SAT prep"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "/act-prep",
								"aria-current": exam === "ACT" ? "page" : void 0,
								children: "ACT prep"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "/college-planning",
								children: "College planning"
							})
						]
					}),
					/* @__PURE__ */ jsxs("a", {
						className: "button button--small button--dark",
						href: loggedIn ? "/dashboard" : "/login",
						children: [
							loggedIn ? "Open dashboard" : "Log in",
							" ",
							/* @__PURE__ */ jsx(ArrowRight, { size: 15 })
						]
					})
				]
			}),
			/* @__PURE__ */ jsxs("main", { children: [
				/* @__PURE__ */ jsxs("section", {
					className: "hero exam-hero",
					children: [
						/* @__PURE__ */ jsx("div", { className: "hero-glow hero-glow--one" }),
						/* @__PURE__ */ jsx("div", { className: "hero-glow hero-glow--two" }),
						/* @__PURE__ */ jsxs("svg", {
							className: "hero-route",
							viewBox: "0 0 620 420",
							"aria-hidden": "true",
							children: [
								/* @__PURE__ */ jsx("path", { d: "M22 355 C115 355 103 205 214 205 S318 72 420 72 S497 204 598 204" }),
								/* @__PURE__ */ jsx("circle", {
									cx: "22",
									cy: "355",
									r: "6"
								}),
								/* @__PURE__ */ jsx("circle", {
									cx: "214",
									cy: "205",
									r: "6"
								}),
								/* @__PURE__ */ jsx("circle", {
									cx: "420",
									cy: "72",
									r: "6"
								}),
								/* @__PURE__ */ jsx("circle", {
									cx: "598",
									cy: "204",
									r: "6"
								})
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "hero-copy",
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "eyebrow",
									children: [
										/* @__PURE__ */ jsx("span", {}),
										" ",
										d.eyebrow
									]
								}),
								/* @__PURE__ */ jsx("h1", { children: d.title }),
								/* @__PURE__ */ jsx("p", {
									className: "exam-promise",
									children: exam === "ACT" ? "Your goal. Five clear next steps." : "A clear path to your next best."
								}),
								/* @__PURE__ */ jsx("p", {
									className: "hero-tagline",
									children: d.intro
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "hero-actions",
									children: [/* @__PURE__ */ jsxs("a", {
										className: "button button--primary",
										href: destination,
										children: [
											loggedIn ? "Continue your path" : d.primary,
											" ",
											/* @__PURE__ */ jsx(ArrowRight, { size: 18 })
										]
									}), /* @__PURE__ */ jsx("a", {
										className: "button button--quiet",
										href: "#how-it-works",
										children: "See how it works"
									})]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "hero-signal",
									children: [
										/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "01" }), " Find your focus"] }),
										/* @__PURE__ */ jsx("i", {}),
										/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "02" }), " Build the skill"] }),
										/* @__PURE__ */ jsx("i", {}),
										/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "03" }), " See your progress"] })
									]
								})
							]
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "product-frame exam-preview",
							"aria-label": `Illustrative ${exam} study path preview`,
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "frame-float frame-float--signal",
									"aria-hidden": "true",
									children: [/* @__PURE__ */ jsx(Sparkles, {}), " Built around you"]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "frame-top",
									children: [
										/* @__PURE__ */ jsx("span", {}),
										/* @__PURE__ */ jsx("span", {}),
										/* @__PURE__ */ jsx("span", {}),
										/* @__PURE__ */ jsx("div", { children: "mentics.vercel.app" })
									]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "preview-shell",
									children: [/* @__PURE__ */ jsxs("aside", {
										className: "preview-rail",
										children: [
											/* @__PURE__ */ jsx(Brand, {}),
											/* @__PURE__ */ jsxs("div", {
												className: "preview-nav",
												children: [/* @__PURE__ */ jsx(House, { size: 16 }), " Home"]
											}),
											/* @__PURE__ */ jsxs("div", {
												className: "preview-nav active",
												children: [/* @__PURE__ */ jsx(Target, { size: 16 }), " My path"]
											}),
											/* @__PURE__ */ jsxs("div", {
												className: "preview-nav",
												children: [/* @__PURE__ */ jsx(BarChart3, { size: 16 }), " Progress"]
											})
										]
									}), /* @__PURE__ */ jsxs("div", {
										className: "preview-main",
										children: [
											/* @__PURE__ */ jsx("div", {
												className: "preview-heading",
												children: /* @__PURE__ */ jsxs("div", { children: [
													/* @__PURE__ */ jsxs("small", { children: [d.heroCard.label, " · EXAMPLE"] }),
													/* @__PURE__ */ jsx("h2", { children: d.heroCard.title }),
													/* @__PURE__ */ jsx("p", { children: d.heroCard.detail })
												] })
											}),
											/* @__PURE__ */ jsx("ol", {
												className: "exam-path",
												children: d.heroCard.steps.map((step, index) => /* @__PURE__ */ jsxs("li", {
													className: index === 2 ? "is-current" : "",
													children: [
														/* @__PURE__ */ jsx("b", { children: index < 2 ? /* @__PURE__ */ jsx(Check, { size: 15 }) : String(index + 1).padStart(2, "0") }),
														/* @__PURE__ */ jsxs("span", { children: [index === 2 && /* @__PURE__ */ jsx("small", { children: "UP NEXT" }), step] }),
														index === 2 && /* @__PURE__ */ jsx(ArrowRight, { size: 17 })
													]
												}, step))
											}),
											/* @__PURE__ */ jsxs("div", {
												className: "exam-preview-note",
												children: [/* @__PURE__ */ jsx(Sparkles, { size: 15 }), " A focused path. Room to adapt."]
											})
										]
									})]
								})
							]
						})
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "trust-strip",
					"aria-label": `${exam} prep highlights`,
					children: [
						/* @__PURE__ */ jsx("span", { children: "A path that adapts" }),
						/* @__PURE__ */ jsx("span", { children: "Focused daily action" }),
						/* @__PURE__ */ jsx("span", { children: "Progress you can see" }),
						/* @__PURE__ */ jsx("span", { children: "Guidance when you need it" })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "landing-facts",
					"aria-label": `${exam} prep at a glance`,
					children: [
						/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("strong", { children: "5" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "steps at a time" }), /* @__PURE__ */ jsx("small", { children: "A clear starting point and a finish line you can reach." })] })] }),
						/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("strong", { children: exam }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "your test, your focus" }), /* @__PURE__ */ jsx("small", { children: "Keep your goals, study plan, and scores connected." })] })] }),
						/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("strong", { children: "1" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "next useful move" }), /* @__PURE__ */ jsx("small", { children: "Spend less time deciding and more time making progress." })] })] })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "section process story-chapter",
					"data-chapter": "01",
					id: "how-it-works",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "section-heading",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " THE MENTICS METHOD"]
							}),
							/* @__PURE__ */ jsx("h2", { children: d.methodTitle }),
							/* @__PURE__ */ jsx("p", { children: d.methodIntro })
						]
					}), /* @__PURE__ */ jsx("div", {
						className: "process-grid",
						children: d.method.map(([number, title, copy], index) => {
							const Icon = methodIcons[index];
							return /* @__PURE__ */ jsxs("article", { children: [
								/* @__PURE__ */ jsx("b", { children: number }),
								/* @__PURE__ */ jsx(Icon, {}),
								/* @__PURE__ */ jsx("h3", { children: title }),
								/* @__PURE__ */ jsx("p", { children: copy })
							] }, number);
						})
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "section platform story-chapter",
					"data-chapter": "02",
					id: "platform",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "platform-copy",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [
									/* @__PURE__ */ jsx("span", {}),
									" YOUR ",
									exam,
									" WORKSPACE"
								]
							}),
							/* @__PURE__ */ jsx("h2", { children: d.featureTitle }),
							/* @__PURE__ */ jsx("p", { children: exam === "SAT" ? "Learn the concept, put it into practice, and understand what to work on next." : "Give your study time a clear purpose, with your goals and progress in one place." }),
							/* @__PURE__ */ jsxs("a", {
								href: destination,
								children: [
									"Build your ",
									exam,
									" path ",
									/* @__PURE__ */ jsx(ArrowRight, { size: 17 })
								]
							})
						]
					}), /* @__PURE__ */ jsx("div", {
						className: "feature-stack",
						children: d.features.map(([Icon, title, copy]) => /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(Icon, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: title }), /* @__PURE__ */ jsx("small", { children: copy })] })] }, title))
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "section exam-detail story-chapter",
					"data-chapter": "03",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "section-heading",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "eyebrow",
							children: [/* @__PURE__ */ jsx("span", {}), " BUILT AROUND REAL PROGRESS"]
						}), /* @__PURE__ */ jsx("h2", { children: d.detailTitle })]
					}), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("p", { children: d.detailCopy }), /* @__PURE__ */ jsxs("a", {
						className: "button button--primary",
						href: destination,
						children: ["Find your next step ", /* @__PURE__ */ jsx(ArrowRight, { size: 18 })]
					})] })]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "section faq story-chapter",
					"data-chapter": "04",
					id: "faq",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "section-heading",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "eyebrow",
							children: [/* @__PURE__ */ jsx("span", {}), " BEFORE YOU START"]
						}), /* @__PURE__ */ jsx("h2", { children: "Good questions." })]
					}), d.faq.map(([q, a]) => /* @__PURE__ */ jsxs("details", { children: [/* @__PURE__ */ jsxs("summary", { children: [q, /* @__PURE__ */ jsx(Plus, { size: 18 })] }), /* @__PURE__ */ jsx("p", { children: a })] }, q))]
				}),
				/* @__PURE__ */ jsx("section", {
					className: "closing",
					children: /* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsx(Brand, { inverse: true }),
						/* @__PURE__ */ jsxs("h2", { children: [
							"Your ",
							exam,
							" goal starts here."
						] }),
						/* @__PURE__ */ jsx("p", { children: "Make the next move clear. Then make it count." }),
						/* @__PURE__ */ jsxs("a", {
							className: "button button--light",
							href: destination,
							children: [
								loggedIn ? "Open dashboard" : "Build your free path",
								" ",
								/* @__PURE__ */ jsx(ArrowRight, { size: 18 })
							]
						})
					] })
				})
			] }),
			/* @__PURE__ */ jsxs("footer", { children: [
				/* @__PURE__ */ jsx(Brand, {}),
				/* @__PURE__ */ jsx("span", { children: "© 2026 Mentics. All rights reserved." }),
				/* @__PURE__ */ jsxs("div", { children: [
					productLinks.map(([href, label]) => /* @__PURE__ */ jsx("a", {
						href,
						"aria-current": href === `/${kind}` ? "page" : void 0,
						children: label
					}, href)),
					/* @__PURE__ */ jsx("a", {
						href: "/terms",
						children: "Terms"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "/privacy",
						children: "Privacy"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "mailto:thementicsapp@gmail.com",
						children: "Contact"
					})
				] }),
				/* @__PURE__ */ jsx("p", {
					className: "exam-disclaimer",
					children: "Mentics is independent and is not affiliated with or endorsed by College Board or ACT, Inc. SAT is a registered trademark of College Board. ACT is a registered trademark of ACT, Inc."
				})
			] })
		]
	});
}
function Landing() {
	const loggedIn = useClientOnly(boot.data.isLoggedIn, false);
	useEffect(() => {
		const nodes = [...document.querySelectorAll(".landing-facts > div,.story-chapter,.section-heading,.process-grid article,.signal-story-visual,.signal-story-beats article,.journey-showcase-copy,.journey-demo,.platform-copy,.feature-stack > div,.suite-heading,.suite-grid article,.week-heading,.week-flow article,.faq details,.closing")];
		nodes.forEach((node) => node.classList.add("mx-reveal"));
		if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
			nodes.forEach((node) => node.classList.add("is-visible"));
			return;
		}
		const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
			if (entry.isIntersecting) {
				entry.target.classList.add("is-visible");
				observer.unobserve(entry.target);
			}
		}), {
			threshold: .12,
			rootMargin: "0px 0px -7% 0px"
		});
		nodes.forEach((node) => observer.observe(node));
		return () => observer.disconnect();
	}, []);
	return /* @__PURE__ */ jsxs("div", {
		className: "landing home-landing",
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "story-progress",
				"aria-hidden": "true"
			}),
			/* @__PURE__ */ jsx(Starfield, {}),
			/* @__PURE__ */ jsxs("header", {
				className: "public-nav",
				children: [
					/* @__PURE__ */ jsx(Brand, {}),
					/* @__PURE__ */ jsxs("nav", {
						"aria-label": "Main navigation",
						children: [
							/* @__PURE__ */ jsx("a", {
								href: "#how-it-works",
								children: "How it works"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "#platform",
								children: "Platform"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "#suite",
								children: "Suite"
							}),
							/* @__PURE__ */ jsx("a", {
								href: "/sat-prep",
								children: "SAT prep"
							})
						]
					}),
					/* @__PURE__ */ jsxs("a", {
						className: "button button--small button--dark",
						href: loggedIn ? "/dashboard" : "/login",
						children: [
							loggedIn ? "Open dashboard" : "Log in",
							" ",
							/* @__PURE__ */ jsx(ArrowRight, { size: 15 })
						]
					})
				]
			}),
			/* @__PURE__ */ jsxs("main", { children: [
				/* @__PURE__ */ jsx(HomeHero, { loggedIn }),
				/* @__PURE__ */ jsxs("section", {
					className: "trust-strip",
					children: [
						/* @__PURE__ */ jsx("span", { children: "A path that adapts" }),
						/* @__PURE__ */ jsx("span", { children: "Focused daily action" }),
						/* @__PURE__ */ jsx("span", { children: "Progress you can see" }),
						/* @__PURE__ */ jsx("span", { children: "Guidance when you need it" })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "landing-facts",
					"aria-label": "Mentics at a glance",
					children: [
						/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("strong", { children: "5" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "steps at a time" }), /* @__PURE__ */ jsx("small", { children: "Enough direction to move. Never enough noise to freeze." })] })] }),
						/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("strong", { children: "2" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "connected tracks" }), /* @__PURE__ */ jsx("small", { children: "Test preparation and college planning, finally in one rhythm." })] })] }),
						/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("strong", { children: "1" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "place to keep moving" }), /* @__PURE__ */ jsx("small", { children: "Your plan, practice, feedback, progress, and people." })] })] })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "section process story-chapter",
					"data-chapter": "01",
					id: "how-it-works",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "section-heading",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " THE MENTICS METHOD"]
							}),
							/* @__PURE__ */ jsx("h2", { children: "Clarity changes everything." }),
							/* @__PURE__ */ jsx("p", { children: "Mentics turns a distant goal into the next right move—then learns from what happens." })
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "process-grid",
						children: [
							/* @__PURE__ */ jsxs("article", { children: [
								/* @__PURE__ */ jsx("b", { children: "01" }),
								/* @__PURE__ */ jsx(Target, {}),
								/* @__PURE__ */ jsx("h3", { children: "Tell us where you are" }),
								/* @__PURE__ */ jsx("p", { children: "Share your goals, timing, strengths, and the areas that need attention." })
							] }),
							/* @__PURE__ */ jsxs("article", { children: [
								/* @__PURE__ */ jsx("b", { children: "02" }),
								/* @__PURE__ */ jsx(Sparkles, {}),
								/* @__PURE__ */ jsx("h3", { children: "Get a five-step path" }),
								/* @__PURE__ */ jsx("p", { children: "Receive a focused roadmap built around your actual priorities—not a generic checklist." })
							] }),
							/* @__PURE__ */ jsxs("article", { children: [
								/* @__PURE__ */ jsx("b", { children: "03" }),
								/* @__PURE__ */ jsx(BarChart3, {}),
								/* @__PURE__ */ jsx("h3", { children: "Improve with evidence" }),
								/* @__PURE__ */ jsx("p", { children: "Complete work, track results, and let every new path build on real progress." })
							] })
						]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "signal-story story-chapter",
					"data-chapter": "02",
					"aria-labelledby": "signal-story-title",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "signal-story-intro",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " FROM AMBITION TO ACTION"]
							}),
							/* @__PURE__ */ jsx("h2", {
								id: "signal-story-title",
								children: "Mentics turns uncertainty into momentum."
							}),
							/* @__PURE__ */ jsx("p", { children: "Not with a giant checklist. With a living path that gets clearer every time you move." })
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "signal-story-layout",
						children: [/* @__PURE__ */ jsx("div", {
							className: "signal-story-visual",
							"aria-hidden": "true",
							children: /* @__PURE__ */ jsxs("div", {
								className: "signal-glass",
								children: [
									/* @__PURE__ */ jsx("span", { className: "signal-glass-shine" }),
									/* @__PURE__ */ jsx("div", { className: "signal-orbit signal-orbit--one" }),
									/* @__PURE__ */ jsx("div", { className: "signal-orbit signal-orbit--two" }),
									/* @__PURE__ */ jsx("div", {
										className: "signal-core",
										children: /* @__PURE__ */ jsx(Target, {})
									}),
									/* @__PURE__ */ jsxs("svg", {
										viewBox: "0 0 440 540",
										children: [
											/* @__PURE__ */ jsx("path", { d: "M220 84 C220 150 104 150 104 242 S336 330 336 418 S220 455 220 490" }),
											/* @__PURE__ */ jsx("circle", {
												cx: "220",
												cy: "84",
												r: "8"
											}),
											/* @__PURE__ */ jsx("circle", {
												cx: "104",
												cy: "242",
												r: "8"
											}),
											/* @__PURE__ */ jsx("circle", {
												cx: "336",
												cy: "418",
												r: "8"
											}),
											/* @__PURE__ */ jsx("circle", {
												cx: "220",
												cy: "490",
												r: "8"
											})
										]
									}),
									/* @__PURE__ */ jsxs("span", {
										className: "signal-tag signal-tag--goal",
										children: [/* @__PURE__ */ jsx("small", { children: "01" }), /* @__PURE__ */ jsx("b", { children: "Your goal" })]
									}),
									/* @__PURE__ */ jsxs("span", {
										className: "signal-tag signal-tag--path",
										children: [/* @__PURE__ */ jsx("small", { children: "02" }), /* @__PURE__ */ jsx("b", { children: "Five clear steps" })]
									}),
									/* @__PURE__ */ jsxs("span", {
										className: "signal-tag signal-tag--proof",
										children: [/* @__PURE__ */ jsx("small", { children: "03" }), /* @__PURE__ */ jsx("b", { children: "Real evidence" })]
									}),
									/* @__PURE__ */ jsxs("span", {
										className: "signal-tag signal-tag--adapt",
										children: [/* @__PURE__ */ jsx("small", { children: "04" }), /* @__PURE__ */ jsx("b", { children: "A smarter next path" })]
									})
								]
							})
						}), /* @__PURE__ */ jsxs("div", {
							className: "signal-story-beats",
							children: [
								/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("span", { children: "01" }), /* @__PURE__ */ jsxs("div", { children: [
									/* @__PURE__ */ jsx("small", { children: "FIND THE SIGNAL" }),
									/* @__PURE__ */ jsx("h3", { children: "Start with what is true now." }),
									/* @__PURE__ */ jsx("p", { children: "Your scores, goals, timing, strengths, and friction become useful context—not another form that disappears into a database." })
								] })] }),
								/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("span", { children: "02" }), /* @__PURE__ */ jsxs("div", { children: [
									/* @__PURE__ */ jsx("small", { children: "MAKE IT FINISHABLE" }),
									/* @__PURE__ */ jsx("h3", { children: "See only the next five moves." }),
									/* @__PURE__ */ jsx("p", { children: "Mentics cuts through the noise and builds a Duolingo-style route where the next useful action is always obvious." })
								] })] }),
								/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("span", { children: "03" }), /* @__PURE__ */ jsxs("div", { children: [
									/* @__PURE__ */ jsx("small", { children: "LEARN FROM THE WORK" }),
									/* @__PURE__ */ jsx("h3", { children: "Every result changes the picture." }),
									/* @__PURE__ */ jsx("p", { children: "Practice, quiz sources, completed tasks, and updated scores become evidence the system can actually use." })
								] })] }),
								/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("span", { children: "04" }), /* @__PURE__ */ jsxs("div", { children: [
									/* @__PURE__ */ jsx("small", { children: "ADAPT WITHOUT STARTING OVER" }),
									/* @__PURE__ */ jsx("h3", { children: "Your path grows with you." }),
									/* @__PURE__ */ jsx("p", { children: "Regenerate when life changes or progress lands. Mentics keeps the context and gives you a sharper next chapter." })
								] })] })
							]
						})]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "journey-showcase story-chapter",
					"data-chapter": "03",
					"aria-labelledby": "journey-title",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "journey-showcase-copy",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow eyebrow--light",
								children: [/* @__PURE__ */ jsx("span", {}), " A PATH YOU CAN FEEL"]
							}),
							/* @__PURE__ */ jsx("h2", {
								id: "journey-title",
								children: "Progress should feel alive."
							}),
							/* @__PURE__ */ jsx("p", { children: "Your next move stays obvious. Finish a step, watch the route open up, and keep your attention on what is ready now—not a wall of future obligations." }),
							/* @__PURE__ */ jsxs("ul", { children: [
								/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx(Check, {}), " One active step keeps the day focused"] }),
								/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx(Zap, {}), " Practice and feedback live inside the route"] }),
								/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx(Trophy, {}), " Milestones make the work worth celebrating"] })
							] }),
							/* @__PURE__ */ jsxs("a", {
								href: loggedIn ? "/dashboard/test-path-view" : "/signup",
								children: ["See your path ", /* @__PURE__ */ jsx(ArrowRight, { size: 17 })]
							})
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "journey-demo",
						"aria-hidden": "true",
						children: [
							/* @__PURE__ */ jsx("div", { className: "journey-demo-glow" }),
							/* @__PURE__ */ jsxs("svg", {
								viewBox: "0 0 420 650",
								children: [/* @__PURE__ */ jsx("path", {
									className: "demo-route-base",
									d: "M210 58 C210 120 105 128 105 200 S315 280 315 350 S105 430 105 500 S210 550 210 598"
								}), /* @__PURE__ */ jsx("path", {
									className: "demo-route-live",
									d: "M210 58 C210 120 105 128 105 200 S315 280 315 350"
								})]
							}),
							[
								{
									x: 50,
									y: 9,
									state: "done",
									label: "Set your baseline",
									icon: /* @__PURE__ */ jsx(Check, {})
								},
								{
									x: 25,
									y: 31,
									state: "done",
									label: "Build the skill",
									icon: /* @__PURE__ */ jsx(Check, {})
								},
								{
									x: 75,
									y: 54,
									state: "current",
									label: "Focused sprint",
									icon: /* @__PURE__ */ jsx(Zap, {})
								},
								{
									x: 25,
									y: 77,
									state: "locked",
									label: "Review the evidence",
									icon: /* @__PURE__ */ jsx(LockKeyhole, {})
								},
								{
									x: 50,
									y: 92,
									state: "milestone",
									label: "Milestone",
									icon: /* @__PURE__ */ jsx(Trophy, {})
								}
							].map((step, index) => /* @__PURE__ */ jsxs("div", {
								className: `demo-step ${step.state}`,
								style: {
									left: `${step.x}%`,
									top: `${step.y}%`
								},
								children: [/* @__PURE__ */ jsx("i", { children: step.icon }), /* @__PURE__ */ jsxs("span", { children: [index === 2 && /* @__PURE__ */ jsx("small", { children: "UP NEXT" }), step.label] })]
							}, step.label))
						]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "battle-landing story-chapter",
					"data-chapter": "04",
					"aria-labelledby": "battle-landing-title",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "battle-landing-copy",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " SAT BATTLE ARENA"]
							}),
							/* @__PURE__ */ jsx("h2", {
								id: "battle-landing-title",
								children: "A faster way to prove what you know."
							}),
							/* @__PURE__ */ jsx("p", { children: "Meet one student in a clean, timed five-question SAT round. Both of you get the same original questions. Accuracy decides it; speed breaks the tie." }),
							/* @__PURE__ */ jsxs("a", {
								className: "button button--primary",
								href: loggedIn ? "/battles" : "/signup",
								children: [
									/* @__PURE__ */ jsx(Swords, {}),
									" ",
									loggedIn ? "Enter the arena" : "Build your path first",
									" ",
									/* @__PURE__ */ jsx(ArrowRight, { size: 17 })
								]
							})
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "battle-landing-preview",
						"aria-hidden": "true",
						children: [
							/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("i", {}), " LIVE ROUND"] }), /* @__PURE__ */ jsxs("strong", { children: [/* @__PURE__ */ jsx(Clock3, {}), " 1:18"] })] }),
							/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsx("small", { children: "QUESTION 3 · ALGEBRA" }),
								/* @__PURE__ */ jsx("b", { children: "If 3x + 8 = 29, what is x?" }),
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("i", { children: "A" }), " 5"] }),
								/* @__PURE__ */ jsxs("span", {
									className: "selected",
									children: [
										/* @__PURE__ */ jsx("i", { children: "B" }),
										" 7 ",
										/* @__PURE__ */ jsx(Check, {})
									]
								}),
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("i", { children: "C" }), " 9"] })
							] }),
							/* @__PURE__ */ jsxs("footer", { children: [
								/* @__PURE__ */ jsxs("span", { children: ["YOU ", /* @__PURE__ */ jsx("b", { children: "2" })] }),
								/* @__PURE__ */ jsx("i", { children: "VS" }),
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "2" }), " RIVAL"] })
							] })
						]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "section platform story-chapter",
					"data-chapter": "05",
					id: "platform",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "platform-copy",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow eyebrow--light",
								children: [/* @__PURE__ */ jsx("span", {}), " ONE FOCUSED WORKSPACE"]
							}),
							/* @__PURE__ */ jsxs("h2", { children: [
								"Less noise.",
								/* @__PURE__ */ jsx("br", {}),
								"More momentum."
							] }),
							/* @__PURE__ */ jsx("p", { children: "Test prep, college planning, progress, and contextual guidance belong in one calm place." }),
							/* @__PURE__ */ jsxs("a", {
								href: loggedIn ? "/dashboard" : "/signup",
								children: ["Explore the platform ", /* @__PURE__ */ jsx(ArrowRight, { size: 17 })]
							})
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "feature-stack",
						children: [
							/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(Target, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "Adaptive paths" }), /* @__PURE__ */ jsx("small", { children: "Five clear steps that respond to your goals and performance." })] })] }),
							/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(MessageCircle, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "Contextual guidance" }), /* @__PURE__ */ jsx("small", { children: "Ask for help without losing the context of what you are working on." })] })] }),
							/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(GraduationCap, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "College planning" }), /* @__PURE__ */ jsx("small", { children: "Turn applications, essays, and deadlines into manageable progress." })] })] }),
							/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(BarChart3, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "Visible progress" }), /* @__PURE__ */ jsx("small", { children: "Track scores, streaks, milestones, and the work behind them." })] })] })
						]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "suite-section story-chapter",
					"data-chapter": "05",
					id: "suite",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "suite-heading",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " THE COMPLETE MENTICS SUITE"]
							}),
							/* @__PURE__ */ jsxs("h2", { children: [
								"Everything your ambition needs.",
								/* @__PURE__ */ jsx("br", {}),
								"Nothing it doesn’t."
							] }),
							/* @__PURE__ */ jsx("p", { children: "The tools already inside Mentics, brought into one expressive workspace." })
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "suite-grid",
						children: [
							/* @__PURE__ */ jsxs("article", {
								className: "suite-path",
								children: [
									/* @__PURE__ */ jsx(Target, {}),
									/* @__PURE__ */ jsx("small", { children: "ADAPTIVE PATHS" }),
									/* @__PURE__ */ jsx("h3", { children: "Five steps. One clear direction." }),
									/* @__PURE__ */ jsx("p", { children: "Personalized SAT, ACT, and college-planning roadmaps that respond to your progress." }),
									/* @__PURE__ */ jsxs("div", {
										className: "mini-road",
										children: [
											/* @__PURE__ */ jsx("i", { children: "1" }),
											/* @__PURE__ */ jsx("span", {}),
											/* @__PURE__ */ jsx("i", { children: "2" }),
											/* @__PURE__ */ jsx("span", {}),
											/* @__PURE__ */ jsx("i", { children: "3" }),
											/* @__PURE__ */ jsx("span", {}),
											/* @__PURE__ */ jsx("i", { children: "4" }),
											/* @__PURE__ */ jsx("span", {}),
											/* @__PURE__ */ jsx("i", { children: "5" })
										]
									})
								]
							}),
							/* @__PURE__ */ jsxs("article", {
								className: "suite-sprint",
								children: [
									/* @__PURE__ */ jsx(Zap, {}),
									/* @__PURE__ */ jsx("small", { children: "FOCUSED SPRINTS" }),
									/* @__PURE__ */ jsx("h3", { children: "Practice with purpose." }),
									/* @__PURE__ */ jsx("p", { children: "Short assessments, strategy articles, and immediate explanations make every session count." })
								]
							}),
							/* @__PURE__ */ jsxs("article", {
								className: "suite-essay",
								children: [
									/* @__PURE__ */ jsx(PenLine, {}),
									/* @__PURE__ */ jsx("small", { children: "ESSAY FEEDBACK" }),
									/* @__PURE__ */ jsx("h3", { children: "Make every word stronger." }),
									/* @__PURE__ */ jsx("p", { children: "Get structured feedback while keeping your voice, story, and ideas unmistakably yours." })
								]
							}),
							/* @__PURE__ */ jsxs("article", {
								className: "suite-progress",
								children: [
									/* @__PURE__ */ jsx(LineChart, {}),
									/* @__PURE__ */ jsx("small", { children: "VISIBLE PROGRESS" }),
									/* @__PURE__ */ jsx("h3", { children: "See the work adding up." }),
									/* @__PURE__ */ jsx("p", { children: "Scores, milestones, history, points, and streaks reveal the pattern behind improvement." })
								]
							}),
							/* @__PURE__ */ jsxs("article", {
								className: "suite-community",
								children: [
									/* @__PURE__ */ jsx(UsersRound, {}),
									/* @__PURE__ */ jsx("small", { children: "COMMUNITY" }),
									/* @__PURE__ */ jsx("h3", { children: "Move forward together." }),
									/* @__PURE__ */ jsx("p", { children: "Ask questions, share approaches, and keep your own progress private." })
								]
							})
						]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "week-section story-chapter",
					"data-chapter": "06",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "week-heading",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " MOMENTUM, NOT BUSYWORK"]
							}),
							/* @__PURE__ */ jsx("h2", { children: "A week inside Mentics." }),
							/* @__PURE__ */ jsx("p", { children: "The plan bends around real student life. Each session has a purpose, a finish line, and a visible place in the bigger picture." })
						]
					}), /* @__PURE__ */ jsx("div", {
						className: "week-flow",
						children: [
							[
								"MON",
								"Find the signal",
								"Check your path and start with the highest-impact move.",
								Target
							],
							[
								"TUE",
								"Practice on purpose",
								"Run a short sprint, then understand every missed question.",
								Zap
							],
							[
								"WED",
								"Make the story stronger",
								"Shape an essay without sanding away your own voice.",
								PenLine
							],
							[
								"THU",
								"Ask while it is fresh",
								"Get guidance with the context of your path still attached.",
								MessageCircle
							],
							[
								"FRI",
								"See what changed",
								"Log the result, close the loop, and unlock what comes next.",
								LineChart
							]
						].map(([day, title, copy, Icon], index) => /* @__PURE__ */ jsxs("article", { children: [
							/* @__PURE__ */ jsx("span", { children: day }),
							/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx(Icon, {}) }),
							/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsxs("small", { children: ["0", index + 1] }),
								/* @__PURE__ */ jsx("h3", { children: title }),
								/* @__PURE__ */ jsx("p", { children: copy })
							] })
						] }, day))
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "section faq story-chapter",
					"data-chapter": "07",
					id: "faq",
					children: [/* @__PURE__ */ jsx("div", {
						className: "section-heading",
						children: /* @__PURE__ */ jsx("h2", { children: "Good questions." })
					}), [
						["Is Mentics free to use?", "Yes. The current early-access product is free and does not require a credit card."],
						["Does it support both SAT and ACT?", "Yes. Your test-prep path can focus on the SAT, ACT, or both."],
						["Can my plan change as I improve?", "Yes. Regenerate a path after new scores, completed work, or a change in goals. Mentics uses that context to plan the next five steps."]
					].map(([q, a]) => /* @__PURE__ */ jsxs("details", { children: [/* @__PURE__ */ jsxs("summary", { children: [q, /* @__PURE__ */ jsx(Plus, { size: 18 })] }), /* @__PURE__ */ jsx("p", { children: a })] }, q))]
				}),
				/* @__PURE__ */ jsx("section", {
					className: "closing",
					children: /* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsx(Brand, { inverse: true }),
						/* @__PURE__ */ jsx("h2", { children: "Know what to do next." }),
						/* @__PURE__ */ jsx("p", { children: "Build a path that makes your ambition feel possible." }),
						/* @__PURE__ */ jsxs("a", {
							className: "button button--light",
							href: loggedIn ? "/dashboard" : "/signup",
							children: [
								loggedIn ? "Open dashboard" : "Get started free",
								" ",
								/* @__PURE__ */ jsx(ArrowRight, { size: 18 })
							]
						})
					] })
				})
			] }),
			/* @__PURE__ */ jsxs("footer", { children: [
				/* @__PURE__ */ jsx(Brand, {}),
				/* @__PURE__ */ jsx("span", { children: "© 2026 Mentics. All rights reserved." }),
				/* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx("a", {
						href: "/ai-sat-prep",
						children: "AI SAT Prep"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "/sat-prep",
						children: "SAT Prep"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "/act-prep",
						children: "ACT Prep"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "/college-planning",
						children: "College Planning"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "/terms",
						children: "Terms"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "/privacy",
						children: "Privacy"
					}),
					/* @__PURE__ */ jsx("a", {
						href: "mailto:thementicsapp@gmail.com",
						children: "Contact"
					})
				] })
			] })
		]
	});
}
function PortalSelector({ open, onClose }) {
	const [warping, setWarping] = useState("");
	const [error, setError] = useState("");
	useEffect(() => {
		document.body.style.overflow = open ? "hidden" : "";
		return () => {
			document.body.style.overflow = "";
		};
	}, [open]);
	const choose = async (type) => {
		setError("");
		setWarping(type);
		const test = type === "test";
		const request = fetch(test ? "/api/test-path-status" : "/api/college-path-status").then((r) => r.ok ? r.json() : Promise.reject(/* @__PURE__ */ new Error("Could not check this path.")));
		try {
			const [data] = await Promise.all([request, new Promise((resolve) => window.setTimeout(resolve, 1450))]);
			window.location.href = data.has_path ? test ? "/dashboard/test-path-view" : "/dashboard/college-path-view" : test ? "/dashboard/test-path-builder" : "/dashboard/college-path-builder";
		} catch (e) {
			setWarping("");
			setError(e.message);
		}
	};
	if (!open && !warping) return null;
	return createPortal(/* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsxs("div", {
		className: `portal-overlay ${open ? "visible" : ""}`,
		role: "dialog",
		"aria-modal": "true",
		"aria-label": "Choose your path",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "portal-heading",
				children: [
					/* @__PURE__ */ jsx("small", { children: "MENTICS PATH BUILDER" }),
					/* @__PURE__ */ jsx("h2", { children: "Choose your path" }),
					/* @__PURE__ */ jsx("p", { children: "Step through the portal that matches what you want to move forward." })
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "portal-pair",
				children: [/* @__PURE__ */ jsxs("button", {
					className: "portal portal--test",
					onClick: () => choose("test"),
					disabled: Boolean(warping),
					children: [/* @__PURE__ */ jsxs("svg", {
						viewBox: "0 0 220 220",
						"aria-hidden": "true",
						children: [
							/* @__PURE__ */ jsx("defs", { children: /* @__PURE__ */ jsxs("radialGradient", {
								id: "portal-test",
								children: [
									/* @__PURE__ */ jsx("stop", {
										offset: "0",
										stopColor: "#c084fc"
									}),
									/* @__PURE__ */ jsx("stop", {
										offset: ".48",
										stopColor: "#7c3aed"
									}),
									/* @__PURE__ */ jsx("stop", {
										offset: "1",
										stopColor: "#312e81"
									})
								]
							}) }),
							/* @__PURE__ */ jsx("circle", {
								cx: "110",
								cy: "110",
								r: "92"
							}),
							/* @__PURE__ */ jsx("circle", {
								cx: "110",
								cy: "110",
								r: "76"
							}),
							/* @__PURE__ */ jsx("circle", {
								cx: "110",
								cy: "110",
								r: "62",
								fill: "url(#portal-test)"
							})
						]
					}), /* @__PURE__ */ jsxs("span", { children: [
						/* @__PURE__ */ jsx(BookOpen, {}),
						/* @__PURE__ */ jsx("b", { children: "Test Prep" }),
						/* @__PURE__ */ jsx("small", { children: "SAT / ACT journey" })
					] })]
				}), /* @__PURE__ */ jsxs("button", {
					className: "portal portal--college",
					onClick: () => choose("college"),
					disabled: Boolean(warping),
					children: [/* @__PURE__ */ jsxs("svg", {
						viewBox: "0 0 220 220",
						"aria-hidden": "true",
						children: [
							/* @__PURE__ */ jsx("defs", { children: /* @__PURE__ */ jsxs("radialGradient", {
								id: "portal-college",
								children: [
									/* @__PURE__ */ jsx("stop", {
										offset: "0",
										stopColor: "#818cf8"
									}),
									/* @__PURE__ */ jsx("stop", {
										offset: ".48",
										stopColor: "#4f46e5"
									}),
									/* @__PURE__ */ jsx("stop", {
										offset: "1",
										stopColor: "#172554"
									})
								]
							}) }),
							/* @__PURE__ */ jsx("circle", {
								cx: "110",
								cy: "110",
								r: "92"
							}),
							/* @__PURE__ */ jsx("circle", {
								cx: "110",
								cy: "110",
								r: "76"
							}),
							/* @__PURE__ */ jsx("circle", {
								cx: "110",
								cy: "110",
								r: "62",
								fill: "url(#portal-college)"
							})
						]
					}), /* @__PURE__ */ jsxs("span", { children: [
						/* @__PURE__ */ jsx(GraduationCap, {}),
						/* @__PURE__ */ jsx("b", { children: "College Plan" }),
						/* @__PURE__ */ jsx("small", { children: "Applications and more" })
					] })]
				})]
			}),
			error && /* @__PURE__ */ jsx("p", {
				className: "portal-error",
				children: error
			}),
			/* @__PURE__ */ jsx("button", {
				className: "portal-close",
				onClick: onClose,
				"aria-label": "Close path selector",
				children: /* @__PURE__ */ jsx(X, {})
			})
		]
	}), warping && /* @__PURE__ */ jsxs("div", {
		className: "warp-overlay",
		children: [/* @__PURE__ */ jsx(Starfield, {
			warp: true,
			tone: warping === "college" ? "indigo" : "violet"
		}), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(Brand, { inverse: true }), /* @__PURE__ */ jsx("p", { children: "Connecting to your path" })] })]
	})] }), document.body);
}
function Dashboard() {
	const d = boot.data;
	const trophies = d.earnedAchievements || [];
	const [suggestion, setSuggestion] = useState("Reviewing your latest progress…");
	const [portalOpen, setPortalOpen] = useState(false);
	useEffect(() => {
		fetch("/api/get-suggestion").then((r) => r.json()).then((x) => setSuggestion(x.suggestion || "Your next clear step is waiting.")).catch(() => setSuggestion("Keep the next step small, specific, and finishable."));
	}, []);
	const chart = d.activityData?.data || [
		0,
		0,
		0,
		0,
		0,
		0,
		0
	];
	const max = Math.max(...chart, 1);
	const first = String(d.name || "Student").split(" ")[0];
	const today = new Intl.DateTimeFormat(void 0, {
		weekday: "long",
		month: "long",
		day: "numeric",
		year: "numeric"
	}).format(/* @__PURE__ */ new Date());
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main dashboard-page dashboard-original",
			children: [
				/* @__PURE__ */ jsxs("section", {
					className: "dashboard-welcome",
					children: [/* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsx("small", { children: today }),
						/* @__PURE__ */ jsxs("h1", { children: ["Welcome back, ", /* @__PURE__ */ jsx("span", { children: first })] }),
						/* @__PURE__ */ jsx("p", { children: "Your dashboard is ready. Let’s build momentum." })
					] }), /* @__PURE__ */ jsxs("div", {
						className: "dashboard-totals",
						children: [/* @__PURE__ */ jsxs("span", { children: [
							/* @__PURE__ */ jsx(Flame, {}),
							/* @__PURE__ */ jsx("b", { children: d.gameStats?.streak || 0 }),
							/* @__PURE__ */ jsx("small", { children: "DAY STREAK" })
						] }), /* @__PURE__ */ jsxs("span", { children: [
							/* @__PURE__ */ jsx(Zap, {}),
							/* @__PURE__ */ jsx("b", { children: d.gameStats?.points || 0 }),
							/* @__PURE__ */ jsx("small", { children: "POINTS" })
						] })]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "command-grid",
					children: [
						/* @__PURE__ */ jsxs("button", {
							className: "path-launcher",
							onClick: () => setPortalOpen(true),
							children: [
								/* @__PURE__ */ jsx("span", { className: "path-launcher-grid" }),
								/* @__PURE__ */ jsxs("div", { children: [
									/* @__PURE__ */ jsx("small", { children: "THE CORE EXPERIENCE" }),
									/* @__PURE__ */ jsx("h2", { children: "Path Builder" }),
									/* @__PURE__ */ jsx("p", { children: "Launch the Mentics portal to generate or update your personalized roadmap." }),
									/* @__PURE__ */ jsxs("b", { children: ["Open portal ", /* @__PURE__ */ jsx(ArrowRight, {})] })
								] }),
								/* @__PURE__ */ jsxs("div", {
									className: "path-radar",
									children: [
										/* @__PURE__ */ jsx("i", {}),
										/* @__PURE__ */ jsx("i", {}),
										/* @__PURE__ */ jsx("i", {}),
										/* @__PURE__ */ jsx(Target, {})
									]
								})
							]
						}),
						/* @__PURE__ */ jsxs("a", {
							className: "dash-module battle-dashboard-card",
							href: "/battles",
							children: [/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsx("small", { children: "SAT BATTLE ARENA" }),
								/* @__PURE__ */ jsx("h2", { children: "Put your speed to the test." }),
								/* @__PURE__ */ jsx("p", { children: "Race a matched student through five SAT-style questions. Accuracy wins; speed settles the tie." }),
								/* @__PURE__ */ jsxs("b", { children: ["Enter the arena ", /* @__PURE__ */ jsx(ArrowRight, {})] })
							] }), /* @__PURE__ */ jsxs("span", { children: [
								/* @__PURE__ */ jsx(Swords, {}),
								/* @__PURE__ */ jsx("i", { children: "1:1" }),
								/* @__PURE__ */ jsx("small", { children: "LIVE" })
							] })]
						}),
						/* @__PURE__ */ jsx(ProgressTile, {
							type: "test",
							value: d.testPrepCompleted || 0
						}),
						/* @__PURE__ */ jsx(ProgressTile, {
							type: "college",
							value: d.collegePlanningCompleted || 0
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "dash-module activity-module",
							children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: "ACTIVITY TREND" }), /* @__PURE__ */ jsx("h2", { children: "Focus intensity" })] }), /* @__PURE__ */ jsx(BarChart3, {})] }), /* @__PURE__ */ jsx("div", {
								className: "command-chart",
								children: chart.map((v, i) => /* @__PURE__ */ jsxs("div", { children: [
									/* @__PURE__ */ jsx("b", { children: v }),
									/* @__PURE__ */ jsx("i", { style: { height: `${Math.max(7, v / max * 100)}%` } }),
									/* @__PURE__ */ jsx("small", { children: d.activityData?.labels?.[i] })
								] }, i))
							})]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "dash-module vital-module",
							children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsx("small", { children: "VITAL STATS" }), /* @__PURE__ */ jsx("a", {
								href: "/dashboard/stats/edit",
								children: "Update"
							})] }), /* @__PURE__ */ jsxs("dl", { children: [
								/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "GPA" }), /* @__PURE__ */ jsx("dd", { children: d.gpa })] }),
								/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "SAT" }), /* @__PURE__ */ jsx("dd", { children: d.satTotal })] }),
								/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", { children: "ACT" }), /* @__PURE__ */ jsx("dd", { children: d.actAverage })] })
							] })]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "dash-module insight-module",
							children: [/* @__PURE__ */ jsx("div", {
								className: "countdown",
								children: d.testDateInfo?.days_left != null ? /* @__PURE__ */ jsxs(Fragment, { children: [
									/* @__PURE__ */ jsx("strong", { children: d.testDateInfo.days_left }),
									/* @__PURE__ */ jsxs("span", { children: ["DAYS TO ", d.testDateInfo.test_type] }),
									/* @__PURE__ */ jsx("small", { children: d.testDateInfo.date_str })
								] }) : /* @__PURE__ */ jsxs(Fragment, { children: [
									/* @__PURE__ */ jsx(CalendarDays, {}),
									/* @__PURE__ */ jsx("span", { children: "NO TEST DATE SET" }),
									/* @__PURE__ */ jsx("a", {
										href: "/dashboard/test-path-builder",
										children: "Set your date"
									})
								] })
							}), /* @__PURE__ */ jsxs("div", {
								className: "insight",
								children: [
									/* @__PURE__ */ jsx(Brain, {}),
									/* @__PURE__ */ jsx("small", { children: "MENTICS INSIGHT" }),
									/* @__PURE__ */ jsx("p", { children: suggestion })
								]
							})]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "dash-module updates-module",
							children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: "LATEST SIGNALS" }), /* @__PURE__ */ jsx("h2", { children: "Recent updates" })] }), /* @__PURE__ */ jsx(Clock3, {})] }), /* @__PURE__ */ jsx("div", { children: d.recentActivities?.length ? d.recentActivities.slice(0, 4).map((a, i) => /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx(Check, {}) }), /* @__PURE__ */ jsxs("p", { children: [/* @__PURE__ */ jsx("b", { children: activityTitle(a) }), /* @__PURE__ */ jsx("small", { children: activityDetail(a) })] })] }, i)) : /* @__PURE__ */ jsxs("div", {
								className: "empty-state",
								children: [/* @__PURE__ */ jsx(Target, {}), /* @__PURE__ */ jsx("p", { children: "Your completed work will show up here." })]
							}) })]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: `dash-module trophies-module ${trophies.length ? "" : "trophies-module--empty"}`,
							children: [
								/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: "MILESTONES" }), /* @__PURE__ */ jsx("h2", { children: "Trophies" })] }), trophies.length ? /* @__PURE__ */ jsxs("span", {
									className: "trophy-total",
									children: [trophies.length, " earned"]
								}) : /* @__PURE__ */ jsx(Award, {})] }),
								/* @__PURE__ */ jsx("div", {
									className: "trophy-list",
									children: trophies.length ? trophies.slice(0, 6).map((item) => /* @__PURE__ */ jsxs("div", {
										className: "trophy-item",
										children: [/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx(Trophy, {}) }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: item.title }), /* @__PURE__ */ jsx("small", { children: item.description })] })]
									}, item.id)) : /* @__PURE__ */ jsxs("div", {
										className: "trophy-empty",
										children: [/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx(Trophy, {}) }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "No trophies yet" }), /* @__PURE__ */ jsx("small", { children: "Complete your first path task to earn one." })] })]
									})
								}),
								/* @__PURE__ */ jsxs("a", {
									href: "/points",
									children: ["View points & achievements ", /* @__PURE__ */ jsx(ArrowRight, {})]
								})
							]
						})
					]
				}),
				/* @__PURE__ */ jsx(PortalSelector, {
					open: portalOpen,
					onClose: () => setPortalOpen(false)
				})
			]
		})
	});
}
function ProgressTile({ type, value }) {
	const test = type === "test";
	const Icon = test ? BookOpen : GraduationCap;
	return /* @__PURE__ */ jsxs("a", {
		className: `dash-module progress-tile progress-tile--${type}`,
		href: test ? "/dashboard/test-path-view" : "/dashboard/college-path-view",
		children: [
			/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsx(Icon, {}), /* @__PURE__ */ jsx("small", { children: test ? "TEST PREP" : "COLLEGE PLAN" })] }),
			/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsxs("strong", { children: [/* @__PURE__ */ jsx("b", { children: value }), /* @__PURE__ */ jsx("i", { children: "/5" })] }), /* @__PURE__ */ jsx("span", { children: value === 5 ? "PATH COMPLETE" : "TASKS DONE" })] }),
			/* @__PURE__ */ jsx("em", { children: /* @__PURE__ */ jsx("i", { style: { width: `${value / 5 * 100}%` } }) })
		]
	});
}
function activityTitle(a) {
	return {
		task_completed: "Task completed",
		path_generated: "New path created",
		stat_updated: "Progress updated",
		task_added: "Task added"
	}[a.type] || "Progress recorded";
}
function activityDetail(a) {
	return a.details?.description || a.details?.stat_name || "A step forward on your Mentics path";
}
function Markdown({ children }) {
	const html = useMemo(() => DOMPurify.sanitize(marked.parse(children || "", { breaks: true })), [children]);
	return /* @__PURE__ */ jsx("div", {
		className: "markdown",
		dangerouslySetInnerHTML: { __html: html }
	});
}
var nodeKinds = {
	lesson: {
		label: "Lesson",
		icon: BookOpen,
		cta: "Start lesson",
		resume: "Continue lesson",
		blurb: "Mentics teaches this skill step by step, checking your understanding as you go."
	},
	practice_sprint: {
		label: "Practice",
		icon: Zap,
		cta: "Start practice",
		resume: "Keep practicing",
		blurb: "Short drill on what you just learned. Instant feedback on every answer."
	},
	quiz: {
		label: "Review",
		icon: Brain,
		cta: "Start review",
		resume: "Keep reviewing",
		blurb: "A mixed review of everything this unit covered."
	},
	boss_battle: {
		label: "Boss battle",
		icon: Trophy,
		cta: "Open official test",
		resume: "Open official test",
		blurb: "A full, timed official practice test. Log your score when you finish."
	},
	milestone: {
		label: "Milestone",
		icon: Award,
		cta: "Start this milestone",
		resume: "Finish this milestone",
		blurb: "Real work outside Mentics. Log what you produced and the next unit builds on it."
	}
};
function taskKind(task) {
	if (task.node_type && nodeKinds[task.node_type]) return task.node_type;
	if (nodeKinds[task.task_format]) return task.task_format;
	if (task.type === "milestone" || String(task.description).toLowerCase().includes("boss battle")) return "boss_battle";
	return null;
}
function firstLink(text) {
	const m = /\[([^\]]+)\]\(([^)]+)\)/.exec(String(text || ""));
	return m ? m[2] : null;
}
function PathPage() {
	const category = boot.data.category;
	const isTest = category === "Test Prep";
	const [tasks, setTasks] = useState([]);
	const [loading, setLoading] = useState(true);
	const [regenerating, setRegenerating] = useState(false);
	const [error, setError] = useState("");
	const [selected, setSelected] = useState(null);
	const [chatOpen, setChatOpen] = useState(() => window.matchMedia("(min-width: 1050px)").matches);
	const [adding, setAdding] = useState(false);
	const [essayOpen, setEssayOpen] = useState(false);
	const pathRequest = useRef(0);
	const builder = isTest ? "/dashboard/test-path-builder" : "/dashboard/college-path-builder";
	const loadTasks = async (regenerate = false) => {
		const requestId = ++pathRequest.current;
		setLoading(true);
		setRegenerating(regenerate);
		setError("");
		try {
			const data = await api(`/api/tasks?category=${encodeURIComponent(category)}`, regenerate ? { method: "POST" } : {});
			if (!Array.isArray(data)) throw new Error("Your path could not be loaded.");
			if (requestId === pathRequest.current) setTasks(data.map(normalizeTask));
		} catch (e) {
			if (requestId === pathRequest.current) setError(e.message);
		} finally {
			if (requestId === pathRequest.current) {
				setLoading(false);
				setRegenerating(false);
			}
		}
	};
	useEffect(() => {
		const requestId = ++pathRequest.current;
		let mounted = true;
		api(`/api/tasks?category=${encodeURIComponent(category)}`).then((data) => {
			if (!Array.isArray(data)) throw new Error("Your path could not be loaded.");
			if (mounted && requestId === pathRequest.current) setTasks(data.map(normalizeTask));
		}).catch((e) => {
			if (mounted && requestId === pathRequest.current) setError(e.message);
		}).finally(() => {
			if (mounted && requestId === pathRequest.current) setLoading(false);
		});
		return () => {
			mounted = false;
		};
	}, [category]);
	useEffect(() => {
		const desktop = window.matchMedia("(min-width: 1050px)");
		const keepPathVisible = (event) => {
			if (!event.matches) setChatOpen(false);
		};
		keepPathVisible(desktop);
		desktop.addEventListener("change", keepPathVisible);
		return () => desktop.removeEventListener("change", keepPathVisible);
	}, []);
	const coreTasks = tasks.filter((t) => !t.is_user_added);
	const completed = coreTasks.filter((t) => t.is_completed).length;
	const progressTotal = coreTasks.length || 5;
	const activeIndex = tasks.findIndex((t) => !t.is_completed);
	const journeyHeight = Math.max(790, 180 + (tasks.length - 1) * 155);
	const journeyXs = [
		320,
		170,
		320,
		470,
		320
	];
	const journeyPoints = tasks.map((_, index) => ({
		x: journeyXs[index % journeyXs.length],
		y: 90 + index * 155
	}));
	const journeyCurve = journeyPoints.reduce((path, point, index) => {
		if (index === 0) return `M ${point.x} ${point.y}`;
		const previous = journeyPoints[index - 1];
		const mid = (previous.y + point.y) / 2;
		return `${path} C ${previous.x} ${mid}, ${point.x} ${mid}, ${point.x} ${point.y}`;
	}, "");
	const finishTask = (next, replacementTasks = null) => {
		if (replacementTasks) {
			setTasks(replacementTasks.map(normalizeTask));
			setSelected(null);
			return;
		}
		const coreWasComplete = coreTasks.length === 5 && coreTasks.every((t) => t.is_completed);
		const updated = tasks.map((t) => t.id === next.id ? next : t);
		setTasks(updated);
		setSelected(null);
		const updatedCore = updated.filter((t) => !t.is_user_added);
		if (!coreWasComplete && updatedCore.length === 5 && updatedCore.every((t) => t.is_completed)) window.setTimeout(async () => {
			if (window.confirm("You finished all five steps. Build the next five-step path now?")) await loadTasks(true);
		}, 250);
	};
	return /* @__PURE__ */ jsx(AppShell, {
		name: boot.data.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: `app-main path-page ${chatOpen ? "chat-docked" : ""}`,
			children: [
				/* @__PURE__ */ jsxs("div", {
					className: "path-header",
					children: [/* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsxs("div", {
							className: "eyebrow",
							children: [
								/* @__PURE__ */ jsx("span", {}),
								" ",
								category.toUpperCase()
							]
						}),
						/* @__PURE__ */ jsx("h1", { children: "Your five-step path." }),
						/* @__PURE__ */ jsx("p", { children: "Finish what is in front of you. The path adapts from there." })
					] }), /* @__PURE__ */ jsxs("div", {
						className: "path-header-actions",
						children: [
							!isTest && /* @__PURE__ */ jsxs("button", {
								className: "button button--quiet",
								onClick: () => setEssayOpen(true),
								children: [/* @__PURE__ */ jsx(PenLine, { size: 17 }), " Essay feedback"]
							}),
							!chatOpen && /* @__PURE__ */ jsxs("button", {
								className: "button button--quiet",
								onClick: () => setChatOpen(true),
								children: [/* @__PURE__ */ jsx(MessageCircle, { size: 17 }), " Ask Mentics"]
							}),
							/* @__PURE__ */ jsxs("a", {
								className: "button button--dark",
								href: builder,
								children: ["Edit goals ", /* @__PURE__ */ jsx(ArrowRight, { size: 16 })]
							})
						]
					})]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "path-progress",
					children: [/* @__PURE__ */ jsx("span", { style: { width: `${completed / progressTotal * 100}%` } }), /* @__PURE__ */ jsxs("p", { children: [/* @__PURE__ */ jsxs("b", { children: [
						/* @__PURE__ */ jsx("span", { children: completed }),
						/* @__PURE__ */ jsx("i", { children: "/" }),
						/* @__PURE__ */ jsx("span", { children: progressTotal })
					] }), /* @__PURE__ */ jsx("span", { children: "core steps complete" })] })]
				}),
				error && /* @__PURE__ */ jsxs("div", {
					className: "error-banner",
					children: [error, /* @__PURE__ */ jsx("button", {
						onClick: () => loadTasks(),
						children: "Try again"
					})]
				}),
				loading && !tasks.length ? /* @__PURE__ */ jsx(PathSkeleton, {}) : /* @__PURE__ */ jsxs("section", {
					className: `journey-map ${regenerating ? "journey-map--regenerating" : ""}`,
					style: { height: journeyHeight },
					"aria-label": `${category} learning journey`,
					"aria-busy": regenerating,
					children: [
						/* @__PURE__ */ jsxs("svg", {
							className: "journey-route",
							viewBox: `0 0 640 ${journeyHeight}`,
							preserveAspectRatio: "none",
							"aria-hidden": "true",
							children: [
								/* @__PURE__ */ jsx("defs", { children: /* @__PURE__ */ jsxs("linearGradient", {
									id: "journey-gradient",
									x1: "0",
									y1: "0",
									x2: "0",
									y2: "1",
									children: [/* @__PURE__ */ jsx("stop", {
										offset: "0",
										stopColor: "#8b5cf6"
									}), /* @__PURE__ */ jsx("stop", {
										offset: "1",
										stopColor: "#4f46e5"
									})]
								}) }),
								/* @__PURE__ */ jsx("path", {
									className: "journey-route-shadow",
									d: journeyCurve
								}),
								/* @__PURE__ */ jsx("path", {
									className: "journey-route-progress",
									d: journeyCurve,
									pathLength: "100",
									style: { strokeDasharray: `${tasks.length ? Math.min(100, completed / tasks.length * 100) : 0} 100` }
								})
							]
						}),
						tasks.map((task, index) => {
							const locked = index > activeIndex && activeIndex !== -1;
							const kind = taskKind(task);
							const meta = kind ? nodeKinds[kind] : null;
							const milestone = kind === "boss_battle";
							const NodeIcon = meta?.icon;
							const point = journeyPoints[index];
							const status = task.is_skipped ? "skipped" : task.is_completed ? "completed" : index === activeIndex ? "current" : "locked";
							return /* @__PURE__ */ jsxs("button", {
								disabled: locked,
								style: {
									left: `${point.x / 640 * 100}%`,
									top: point.y
								},
								className: `journey-step ${task.is_completed ? "done" : index === activeIndex ? "current" : "locked"} ${task.is_skipped ? "skipped" : ""} ${milestone ? "milestone" : ""} ${kind ? `journey-step--${kind}` : ""}`,
								onClick: () => setSelected(task),
								"aria-haspopup": "dialog",
								"aria-current": index === activeIndex ? "step" : void 0,
								children: [
									/* @__PURE__ */ jsxs("span", {
										className: "sr-only",
										children: [
											"Step ",
											index + 1,
											", ",
											status,
											locked ? `: ${task.description}` : ".",
											" "
										]
									}),
									index === activeIndex && !task.is_completed && /* @__PURE__ */ jsx("span", {
										className: "journey-next",
										children: "START"
									}),
									/* @__PURE__ */ jsx("span", {
										className: "journey-node",
										children: /* @__PURE__ */ jsx("i", { children: task.is_skipped ? /* @__PURE__ */ jsx(SkipForward, {}) : task.is_completed ? /* @__PURE__ */ jsx(Check, {}) : locked ? /* @__PURE__ */ jsx(LockKeyhole, {}) : NodeIcon ? /* @__PURE__ */ jsx(NodeIcon, {}) : index + 1 })
									}),
									/* @__PURE__ */ jsxs("span", {
										className: `journey-label ${point.x < 320 ? "label-right" : point.x > 320 ? "label-left" : index % 2 ? "label-left" : "label-right"}`,
										children: [
											/* @__PURE__ */ jsx("small", { children: task.is_skipped ? "SKIPPED" : task.is_completed ? "COMPLETED" : task.is_user_added ? "PERSONAL STEP" : meta ? meta.label.toUpperCase() : `STEP ${index + 1}` }),
											/* @__PURE__ */ jsx("b", { children: /* @__PURE__ */ jsx(PlainText, { value: task.description }) }),
											task.skill_label && kind !== "boss_battle" && /* @__PURE__ */ jsx("em", {
												className: "journey-skill",
												children: task.skill_label
											}),
											task.due_date && /* @__PURE__ */ jsxs("em", { children: [
												/* @__PURE__ */ jsx(CalendarDays, {}),
												" ",
												task.due_date
											] })
										]
									})
								]
							}, task.id || index);
						}),
						regenerating && /* @__PURE__ */ jsxs("div", {
							className: "path-regenerating-overlay",
							role: "status",
							"aria-live": "polite",
							children: [/* @__PURE__ */ jsx("span", {
								className: "path-regenerating-orbit",
								children: /* @__PURE__ */ jsx(Sparkles, {})
							}), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "Rebuilding your path" }), /* @__PURE__ */ jsx("small", { children: "Mentics is shaping your next five steps." })] })]
						})
					]
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "path-footer-actions",
					children: [/* @__PURE__ */ jsxs("button", {
						className: "button button--quiet",
						onClick: () => setAdding(true),
						disabled: regenerating,
						children: [/* @__PURE__ */ jsx(Plus, {}), " Add your own step"]
					}), /* @__PURE__ */ jsxs("button", {
						className: "text-button",
						onClick: () => loadTasks(true),
						disabled: regenerating,
						children: [
							/* @__PURE__ */ jsx(RotateCcw, {}),
							" ",
							regenerating ? "Rebuilding your path…" : isTest ? "Regenerate five steps" : "Start next coaching loop"
						]
					})]
				}),
				selected && /* @__PURE__ */ jsx(TaskModal, {
					task: selected,
					category,
					onClose: () => setSelected(null),
					onUpdate: (next) => {
						setTasks((items) => items.map((t) => t.id === next.id ? next : t));
						setSelected(next);
					},
					onCompleted: finishTask,
					onReported: (tasks) => finishTask(null, tasks)
				}),
				adding && /* @__PURE__ */ jsx(AddTask, {
					category,
					onClose: () => setAdding(false),
					onAdded: (t) => {
						setTasks((items) => [...items, normalizeTask(t)]);
						setAdding(false);
					}
				}),
				essayOpen && /* @__PURE__ */ jsx(EssayCoach, { onClose: () => setEssayOpen(false) }),
				/* @__PURE__ */ jsx(ChatPanel, {
					open: chatOpen,
					onClose: () => setChatOpen(false),
					category,
					onNewPath: (items) => setTasks(items.map(normalizeTask))
				}),
				!chatOpen && /* @__PURE__ */ jsxs("button", {
					className: "floating-chat",
					onClick: () => setChatOpen(true),
					"aria-label": "Ask Mentics",
					children: [/* @__PURE__ */ jsx(MessageCircle, {}), /* @__PURE__ */ jsx("span", { children: "Ask Mentics" })]
				})
			]
		})
	});
}
function PlainText({ value }) {
	return /* @__PURE__ */ jsx(Fragment, { children: String(value || "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[*_#`]/g, "") });
}
function normalizeTask(t) {
	return {
		...t,
		is_completed: Boolean(t.is_completed),
		is_skipped: Boolean(t.is_skipped),
		subtasks: Array.isArray(t.subtasks) ? t.subtasks : [],
		task_format: t.task_format || "link"
	};
}
function PathSkeleton() {
	return /* @__PURE__ */ jsx("section", {
		className: "journey-map journey-map--loading",
		children: [
			0,
			1,
			2,
			3,
			4
		].map((i) => /* @__PURE__ */ jsx("span", {
			className: "journey-skeleton skeleton",
			style: {
				left: `${[
					50,
					27,
					50,
					73,
					50
				][i]}%`,
				top: 90 + i * 155
			}
		}, i))
	});
}
function Modal({ children, onClose, wide = false, label = "Dialog" }) {
	const modalRef = useRef(null);
	useEffect(() => {
		const previouslyFocused = document.activeElement;
		const previousOverflow = document.body.style.overflow;
		document.body.style.overflow = "hidden";
		const frame = requestAnimationFrame(() => {
			(modalRef.current?.querySelector("[autofocus], [data-modal-autofocus], button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled)") || modalRef.current)?.focus();
		});
		const handleKeyDown = (event) => {
			if (event.key === "Escape") {
				event.preventDefault();
				onClose();
				return;
			}
			if (event.key !== "Tab" || !modalRef.current) return;
			const focusable = [...modalRef.current.querySelectorAll("button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex=\"-1\"])")].filter((node) => node.getClientRects().length);
			if (!focusable.length) {
				event.preventDefault();
				modalRef.current.focus();
				return;
			}
			const first = focusable[0];
			const last = focusable[focusable.length - 1];
			if (event.shiftKey && (document.activeElement === first || !modalRef.current.contains(document.activeElement))) {
				event.preventDefault();
				last.focus();
			} else if (!event.shiftKey && document.activeElement === last) {
				event.preventDefault();
				first.focus();
			}
		};
		document.addEventListener("keydown", handleKeyDown);
		return () => {
			cancelAnimationFrame(frame);
			document.removeEventListener("keydown", handleKeyDown);
			document.body.style.overflow = previousOverflow;
			if (previouslyFocused instanceof HTMLElement && previouslyFocused.isConnected) previouslyFocused.focus();
		};
	}, [onClose]);
	return createPortal(/* @__PURE__ */ jsx("div", {
		className: "modal-wrap",
		role: "dialog",
		"aria-modal": "true",
		"aria-label": label,
		onPointerDown: (event) => event.target === event.currentTarget && onClose(),
		children: /* @__PURE__ */ jsxs("div", {
			ref: modalRef,
			tabIndex: -1,
			className: `modal ${wide ? "modal--wide" : ""}`,
			children: [/* @__PURE__ */ jsx("button", {
				className: "modal-close",
				onClick: onClose,
				"aria-label": "Close",
				children: /* @__PURE__ */ jsx(X, {})
			}), children]
		})
	}), document.body);
}
var milestoneStats = {
	gpa: {
		label: "New GPA",
		placeholder: "Enter your GPA",
		min: 0,
		max: 5,
		step: .01
	},
	sat_math: {
		label: "New SAT Math score",
		placeholder: "200–800",
		min: 200,
		max: 800
	},
	sat_ebrw: {
		label: "New SAT Reading & Writing score",
		placeholder: "200–800",
		min: 200,
		max: 800
	},
	sat_total: {
		label: "Full SAT practice score",
		placeholder: "400–1600",
		min: 400,
		max: 1600
	},
	act_math: {
		label: "New ACT Math score",
		placeholder: "1–36",
		min: 1,
		max: 36
	},
	act_reading: {
		label: "New ACT Reading score",
		placeholder: "1–36",
		min: 1,
		max: 36
	},
	act_science: {
		label: "New ACT Science score",
		placeholder: "1–36",
		min: 1,
		max: 36
	},
	act_composite: {
		label: "Full ACT practice score",
		placeholder: "1–36",
		min: 1,
		max: 36
	},
	colleges_researched: {
		label: "Colleges researched",
		placeholder: "Enter a number",
		min: 0,
		max: 1e3
	},
	applications_submitted: {
		label: "Applications submitted",
		placeholder: "Enter a number",
		min: 0,
		max: 1e3
	},
	essay_progress: {
		label: "Essay progress",
		placeholder: "1 = draft, 2 = final",
		min: 1,
		max: 2
	}
};
function BossBattle({ task, onClose, onCompleted }) {
	const [detail, setDetail] = useState(null);
	const [scores, setScores] = useState({});
	const [result, setResult] = useState(null);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState("");
	useEffect(() => {
		let live = true;
		api(`/api/boss_battle/${task.id}`).then((d) => {
			if (!live) return;
			setDetail(d);
			setScores(Object.fromEntries(d.sections.map((s) => [s.key, s.previous ? String(s.previous) : ""])));
		}).catch((e) => {
			if (live) setError(e.message);
		});
		return () => {
			live = false;
		};
	}, [task.id]);
	const link = firstLink(task.description) || "https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests";
	const ready = detail && detail.sections.every((s) => String(scores[s.key] ?? "").trim() !== "");
	const submit = async () => {
		setBusy(true);
		setError("");
		try {
			setResult(await api(`/api/boss_battle/${task.id}/result`, {
				method: "POST",
				body: JSON.stringify({ scores })
			}));
		} catch (e) {
			setError(e.message);
		} finally {
			setBusy(false);
		}
	};
	if (result) {
		const up = result.delta != null && result.delta > 0;
		return /* @__PURE__ */ jsx(Modal, {
			onClose: () => onCompleted({
				...task,
				is_completed: true
			}),
			children: /* @__PURE__ */ jsxs("div", {
				className: "boss-result",
				children: [
					/* @__PURE__ */ jsx("div", {
						className: "boss-result-mark",
						children: /* @__PURE__ */ jsx(Trophy, {})
					}),
					/* @__PURE__ */ jsx("div", {
						className: "modal-kicker",
						children: "TEST LOGGED"
					}),
					/* @__PURE__ */ jsxs("h2", { children: [
						result.composite_label,
						" ",
						result.composite
					] }),
					result.delta != null && /* @__PURE__ */ jsxs("p", {
						className: `boss-delta ${up ? "up" : result.delta < 0 ? "down" : ""}`,
						children: [
							up ? "▲" : result.delta < 0 ? "▼" : "—",
							" ",
							Math.abs(result.delta),
							" point",
							Math.abs(result.delta) === 1 ? "" : "s",
							" vs your last ",
							result.composite_label.toLowerCase()
						]
					}),
					/* @__PURE__ */ jsx("div", {
						className: "boss-sections",
						children: Object.entries(result.sections).map(([key, value]) => /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: detail?.sections.find((s) => s.key === key)?.label || key }), /* @__PURE__ */ jsx("b", { children: value })] }, key))
					}),
					result.xp_earned > 0 && /* @__PURE__ */ jsxs("div", {
						className: "player-xp-award",
						children: [
							/* @__PURE__ */ jsx(Zap, {}),
							" +",
							result.xp_earned,
							" XP"
						]
					}),
					/* @__PURE__ */ jsx("p", {
						className: "boss-note",
						children: "Your scores are saved to your stats and tracker, and your next path will be built around whichever section moved least."
					}),
					/* @__PURE__ */ jsxs("button", {
						className: "button button--primary task-start",
						onClick: () => onCompleted({
							...task,
							is_completed: true
						}),
						children: ["Build on this ", /* @__PURE__ */ jsx(ArrowRight, {})]
					})
				]
			})
		});
	}
	return /* @__PURE__ */ jsxs(Modal, {
		onClose,
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "modal-kicker",
				children: ["BOSS BATTLE · ", detail?.test_type || "Official test"]
			}),
			/* @__PURE__ */ jsx("h2", { children: "Take a full official test, then log the score." }),
			/* @__PURE__ */ jsxs("div", {
				className: "task-kind task-kind--boss_battle",
				children: [
					/* @__PURE__ */ jsx("span", {
						className: "task-kind-icon",
						children: /* @__PURE__ */ jsx(Trophy, {})
					}),
					/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "Timed and official" }), /* @__PURE__ */ jsx("p", { children: "Everything this unit drilled in short bursts, under real pacing and fatigue." })] }),
					task.xp_reward ? /* @__PURE__ */ jsxs("span", {
						className: "task-kind-xp",
						children: [
							/* @__PURE__ */ jsx(Zap, {}),
							" ",
							task.xp_reward,
							" XP"
						]
					}) : null
				]
			}),
			/* @__PURE__ */ jsxs("ol", {
				className: "boss-steps",
				children: [/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("span", { children: "1" }), /* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx("b", { children: "Sit the test" }),
					/* @__PURE__ */ jsx("p", { children: "Full length, timed, no interruptions — the score only means something if the conditions are real." }),
					/* @__PURE__ */ jsxs("a", {
						className: "button button--primary task-start",
						href: link,
						target: "_blank",
						rel: "noreferrer",
						children: ["Open official practice ", /* @__PURE__ */ jsx(ArrowRight, {})]
					})
				] })] }), /* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("span", { children: "2" }), /* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx("b", { children: "Log your section scores" }),
					/* @__PURE__ */ jsx("p", { children: "Enter what you actually scored. This is what tells Mentics which section to attack next." }),
					detail ? /* @__PURE__ */ jsx("div", {
						className: "boss-score-grid",
						children: detail.sections.map((s) => /* @__PURE__ */ jsxs("label", { children: [
							s.label,
							/* @__PURE__ */ jsx("input", {
								type: "number",
								inputMode: "numeric",
								min: s.min,
								max: s.max,
								value: scores[s.key] ?? "",
								onChange: (e) => setScores((v) => ({
									...v,
									[s.key]: e.target.value
								})),
								placeholder: `${s.min}–${s.max}`
							}),
							s.previous ? /* @__PURE__ */ jsxs("em", { children: ["last: ", s.previous] }) : null
						] }, s.key))
					}) : /* @__PURE__ */ jsxs("div", {
						className: "boss-score-grid boss-score-grid--loading",
						children: [/* @__PURE__ */ jsx("span", { className: "skeleton" }), /* @__PURE__ */ jsx("span", { className: "skeleton" })]
					})
				] })] })]
			}),
			error && /* @__PURE__ */ jsx("p", {
				className: "form-error",
				children: error
			}),
			/* @__PURE__ */ jsxs("button", {
				className: "button button--primary task-start",
				disabled: !ready || busy,
				onClick: submit,
				children: [
					busy ? "Saving…" : "Log my score and finish",
					" ",
					/* @__PURE__ */ jsx(Check, {})
				]
			}),
			/* @__PURE__ */ jsx("p", {
				className: "boss-note",
				children: "You need a real score to finish this step — it is what the next path is built from."
			})
		]
	});
}
function MilestoneStep({ task, onClose, onCompleted }) {
	const [detail, setDetail] = useState(null);
	const [value, setValue] = useState("");
	const [result, setResult] = useState(null);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState("");
	useEffect(() => {
		let live = true;
		api(`/api/milestone/${task.id}`).then((d) => {
			if (!live) return;
			setDetail(d);
			if (d.previous != null) setValue(String(d.previous));
		}).catch((e) => {
			if (live) setError(e.message);
		});
		return () => {
			live = false;
		};
	}, [task.id]);
	const needsValue = Boolean(detail?.stat_name);
	const ready = detail && (!needsValue || String(value).trim() !== "");
	const submit = async () => {
		setBusy(true);
		setError("");
		try {
			setResult(await api(`/api/milestone/${task.id}/result`, {
				method: "POST",
				body: JSON.stringify({ value: needsValue ? value : null })
			}));
		} catch (e) {
			setError(e.message);
		} finally {
			setBusy(false);
		}
	};
	if (result) {
		const up = result.delta != null && result.delta > 0;
		return /* @__PURE__ */ jsx(Modal, {
			onClose: () => onCompleted({
				...task,
				is_completed: true
			}),
			children: /* @__PURE__ */ jsxs("div", {
				className: "boss-result",
				children: [
					/* @__PURE__ */ jsx("div", {
						className: "boss-result-mark boss-result-mark--milestone",
						children: /* @__PURE__ */ jsx(Award, {})
					}),
					/* @__PURE__ */ jsx("div", {
						className: "modal-kicker",
						children: "MILESTONE COMPLETE"
					}),
					/* @__PURE__ */ jsx("h2", { children: result.value != null ? `${result.value} ${result.unit || ""}`.trim() : "Logged" }),
					up && /* @__PURE__ */ jsxs("p", {
						className: "boss-delta up",
						children: [
							"▲ ",
							result.delta,
							" more than last time"
						]
					}),
					result.xp_earned > 0 && /* @__PURE__ */ jsxs("div", {
						className: "player-xp-award",
						children: [
							/* @__PURE__ */ jsx(Zap, {}),
							" +",
							result.xp_earned,
							" XP"
						]
					}),
					/* @__PURE__ */ jsx("p", {
						className: "boss-note",
						children: "Saved to your stats and tracker. Your next unit is planned from where this leaves you."
					}),
					/* @__PURE__ */ jsxs("button", {
						className: "button button--primary task-start",
						onClick: () => onCompleted({
							...task,
							is_completed: true
						}),
						children: ["Keep going ", /* @__PURE__ */ jsx(ArrowRight, {})]
					})
				]
			})
		});
	}
	return /* @__PURE__ */ jsxs(Modal, {
		onClose,
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "modal-kicker",
				children: "COLLEGE PLANNING · MILESTONE"
			}),
			/* @__PURE__ */ jsx("h2", { children: /* @__PURE__ */ jsx(PlainText, { value: task.description }) }),
			/* @__PURE__ */ jsxs("div", {
				className: "task-kind task-kind--milestone",
				children: [
					/* @__PURE__ */ jsx("span", {
						className: "task-kind-icon",
						children: /* @__PURE__ */ jsx(Award, {})
					}),
					/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: "Real work" }), /* @__PURE__ */ jsx("p", { children: "This is the part an admissions officer actually sees. The unit taught the judgement; now produce the thing." })] }),
					task.xp_reward ? /* @__PURE__ */ jsxs("span", {
						className: "task-kind-xp",
						children: [
							/* @__PURE__ */ jsx(Zap, {}),
							" ",
							task.xp_reward,
							" XP"
						]
					}) : null
				]
			}),
			detail?.objective && /* @__PURE__ */ jsxs("p", {
				className: "task-objective",
				children: [
					/* @__PURE__ */ jsx(Target, {}),
					" ",
					detail.objective
				]
			}),
			task.reason && /* @__PURE__ */ jsxs("div", {
				className: "task-why",
				children: [/* @__PURE__ */ jsx("small", { children: "WHY THIS STEP" }), /* @__PURE__ */ jsx(Markdown, { children: task.reason })]
			}),
			needsValue && /* @__PURE__ */ jsxs("div", {
				className: "milestone-log",
				children: [/* @__PURE__ */ jsxs("label", { children: [detail.label, detail.stat_name === "essay_progress" ? /* @__PURE__ */ jsxs("select", {
					value,
					onChange: (e) => setValue(e.target.value),
					children: [
						/* @__PURE__ */ jsx("option", {
							value: "",
							children: "Choose one…"
						}),
						/* @__PURE__ */ jsx("option", {
							value: "1",
							children: "First full draft done"
						}),
						/* @__PURE__ */ jsx("option", {
							value: "2",
							children: "Revised and final"
						})
					]
				}) : /* @__PURE__ */ jsx("input", {
					type: "number",
					inputMode: "numeric",
					min: detail.min,
					max: detail.max,
					value,
					onChange: (e) => setValue(e.target.value),
					placeholder: `${detail.min}–${detail.max}`
				})] }), detail.previous != null && /* @__PURE__ */ jsxs("em", { children: ["Last recorded: ", detail.previous] })]
			}),
			error && /* @__PURE__ */ jsx("p", {
				className: "form-error",
				children: error
			}),
			/* @__PURE__ */ jsxs("button", {
				className: "button button--primary task-start",
				disabled: !ready || busy,
				onClick: submit,
				children: [
					busy ? "Saving…" : needsValue ? "Log it and finish" : "Mark this done",
					" ",
					/* @__PURE__ */ jsx(Check, {})
				]
			})
		]
	});
}
function CollegeReportStep({ task, onClose, onReported }) {
	const [report, setReport] = useState("");
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState("");
	const submit = async (e) => {
		e.preventDefault();
		if (busy || report.trim().length < 20) return;
		setBusy(true);
		setError("");
		try {
			const result = await api("/api/college_task_report", {
				method: "POST",
				body: JSON.stringify({
					taskId: task.id,
					report
				})
			});
			toast.success("Mentics updated your next step");
			onReported(result.tasks || []);
		} catch (cause) {
			setError(cause.message);
		} finally {
			setBusy(false);
		}
	};
	return /* @__PURE__ */ jsxs(Modal, {
		onClose,
		label: "Report back to Mentics",
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "modal-kicker",
				children: "COLLEGE COACHING LOOP"
			}),
			/* @__PURE__ */ jsx("h2", { children: task.description }),
			/* @__PURE__ */ jsx("p", {
				className: "milestone-copy",
				children: "Do the real work, then tell Mentics what happened. Your report—not a quiz—shapes the next lesson and assignment."
			}),
			task.objective && /* @__PURE__ */ jsxs("div", {
				className: "task-why",
				children: [/* @__PURE__ */ jsx("small", { children: "YOUR ASSIGNMENT" }), /* @__PURE__ */ jsx(Markdown, { children: task.objective })]
			}),
			/* @__PURE__ */ jsxs("form", {
				className: "modal-form college-report-form",
				onSubmit: submit,
				children: [
					/* @__PURE__ */ jsxs("label", { children: ["What did you do, what did you produce, and what felt difficult?", /* @__PURE__ */ jsx("textarea", {
						autoFocus: true,
						value: report,
						onChange: (e) => setReport(e.target.value),
						minLength: 20,
						maxLength: 4e3,
						placeholder: "Example: I compared three colleges on cost and engineering opportunities. Two feel like a fit, but I need help deciding whether the third belongs on my list.",
						disabled: busy
					})] }),
					error && /* @__PURE__ */ jsx("p", {
						className: "form-error",
						role: "alert",
						children: error
					}),
					/* @__PURE__ */ jsxs("button", {
						className: "button button--primary task-start",
						disabled: busy || report.trim().length < 20,
						children: [
							busy ? "Updating your path…" : "Report back and continue",
							" ",
							/* @__PURE__ */ jsx(ArrowRight, {})
						]
					})
				]
			})
		]
	});
}
function TaskModal({ task, category, onClose, onUpdate, onCompleted, onReported }) {
	const [note, setNote] = useState("");
	const [busy, setBusy] = useState(false);
	const [playing, setPlaying] = useState(false);
	const [dueDate, setDueDate] = useState(task.due_date || "");
	const [statPrompt, setStatPrompt] = useState(false);
	const [statValue, setStatValue] = useState("");
	const [error, setError] = useState("");
	const [detailsOpen, setDetailsOpen] = useState(false);
	const stat = milestoneStats[task.stat_to_update];
	const kind = taskKind(task);
	const meta = kind ? nodeKinds[kind] : null;
	const complete = async () => {
		setBusy(true);
		setError("");
		try {
			await api("/api/update_task_status", {
				method: "POST",
				body: JSON.stringify({
					taskId: task.id,
					status: "complete"
				})
			});
			const next = {
				...task,
				is_completed: true
			};
			onUpdate(next);
			if (stat) setStatPrompt(true);
			else onCompleted(next);
		} catch (e) {
			setError(e.message);
		} finally {
			setBusy(false);
		}
	};
	const finishMilestone = async (save) => {
		setBusy(true);
		setError("");
		try {
			if (save) await api("/api/update_stats", {
				method: "POST",
				body: JSON.stringify({
					stat_name: task.stat_to_update,
					stat_value: statValue
				})
			});
			onCompleted({
				...task,
				is_completed: true
			});
		} catch (e) {
			setError(e.message);
		} finally {
			setBusy(false);
		}
	};
	const addNote = async () => {
		if (!note.trim() || busy) return;
		setBusy(true);
		setError("");
		try {
			const r = await api("/api/add_subtask", {
				method: "POST",
				body: JSON.stringify({
					parent_task_id: task.id,
					description: note
				})
			});
			onUpdate({
				...task,
				subtasks: [...task.subtasks, r.subtask]
			});
			setNote("");
		} catch (e) {
			setError(e.message);
		} finally {
			setBusy(false);
		}
	};
	const toggleNote = async (s) => {
		if (busy) return;
		setBusy(true);
		setError("");
		try {
			await api("/api/update_subtask", {
				method: "POST",
				body: JSON.stringify({
					subtaskId: s.id,
					is_completed: !s.is_completed
				})
			});
			onUpdate({
				...task,
				subtasks: task.subtasks.map((x) => x.id === s.id ? {
					...x,
					is_completed: !x.is_completed
				} : x)
			});
		} catch (e) {
			setError(e.message);
		} finally {
			setBusy(false);
		}
	};
	const saveDeadline = async () => {
		try {
			await api("/api/update_task_deadline", {
				method: "POST",
				body: JSON.stringify({
					taskId: task.id,
					dueDate: dueDate || null
				})
			});
			onUpdate({
				...task,
				due_date: dueDate || null
			});
			toast.success("Target date saved");
		} catch (e) {
			toast.error("Could not save the target date", { description: e.message });
		}
	};
	const skipTask = async () => {
		setBusy(true);
		setError("");
		try {
			await api("/api/skip_task", {
				method: "POST",
				body: JSON.stringify({ taskId: task.id })
			});
			const next = {
				...task,
				is_completed: true,
				is_skipped: true
			};
			onUpdate(next);
			onCompleted(next);
		} catch (e) {
			setError(e.message);
		} finally {
			setBusy(false);
		}
	};
	const finishPlay = async () => {
		setPlaying(false);
		if (task.is_completed) {
			onClose();
			return;
		}
		const next = {
			...task,
			is_completed: true
		};
		onUpdate(next);
		if (stat) setStatPrompt(true);
		else onCompleted(next);
	};
	if (kind === "boss_battle" && !task.is_completed) return /* @__PURE__ */ jsx(BossBattle, {
		task,
		onClose,
		onCompleted
	});
	if (kind === "milestone" && category === "College Planning" && !task.is_completed) return /* @__PURE__ */ jsx(CollegeReportStep, {
		task,
		onClose,
		onReported
	});
	if (kind === "milestone" && !task.is_completed) return /* @__PURE__ */ jsx(MilestoneStep, {
		task,
		onClose,
		onCompleted
	});
	if (playing && kind === "lesson") return /* @__PURE__ */ jsx(LessonPlayer, {
		task,
		onClose: () => setPlaying(false),
		onCompleted: finishPlay
	});
	if (playing) return /* @__PURE__ */ jsx(AssessmentPlayer, {
		task,
		onClose: () => setPlaying(false),
		onCompleted: finishPlay
	});
	if (statPrompt) return /* @__PURE__ */ jsxs(Modal, {
		onClose: () => finishMilestone(false),
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "milestone-mark",
				children: /* @__PURE__ */ jsx(Trophy, {})
			}),
			/* @__PURE__ */ jsx("div", {
				className: "modal-kicker",
				children: "MILESTONE COMPLETE"
			}),
			/* @__PURE__ */ jsx("h2", { children: "Record the progress behind the win." }),
			/* @__PURE__ */ jsx("p", {
				className: "milestone-copy",
				children: "This keeps your stats, tracker, and next path grounded in what actually changed."
			}),
			/* @__PURE__ */ jsxs("label", {
				className: "milestone-input",
				children: [stat.label, /* @__PURE__ */ jsx("input", {
					autoFocus: true,
					type: "number",
					value: statValue,
					onChange: (e) => setStatValue(e.target.value),
					placeholder: stat.placeholder,
					min: stat.min,
					max: stat.max,
					step: stat.step || 1
				})]
			}),
			error && /* @__PURE__ */ jsx("p", {
				className: "form-error",
				children: error
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "modal-actions",
				children: [/* @__PURE__ */ jsx("button", {
					className: "button button--quiet",
					onClick: () => finishMilestone(false),
					disabled: busy,
					children: "Skip for now"
				}), /* @__PURE__ */ jsxs("button", {
					className: "button button--primary",
					onClick: () => finishMilestone(true),
					disabled: busy || statValue === "",
					children: ["Save progress ", /* @__PURE__ */ jsx(ArrowRight, {})]
				})]
			})
		]
	});
	const Icon = meta?.icon;
	const bossLink = kind === "boss_battle" ? firstLink(task.description) || "https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests" : null;
	const playable = [
		"lesson",
		"practice_sprint",
		"quiz"
	].includes(kind);
	return /* @__PURE__ */ jsxs(Modal, {
		onClose,
		label: `${meta?.label || "Task"} details`,
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "modal-kicker",
				children: [
					category,
					" · ",
					meta ? meta.label : task.type === "milestone" ? "Milestone" : "Action step",
					task.skill_label ? ` · ${task.skill_label}` : ""
				]
			}),
			/* @__PURE__ */ jsx("h2", { children: /* @__PURE__ */ jsx(PlainText, { value: task.description }) }),
			task.objective && /* @__PURE__ */ jsxs("p", {
				className: "task-objective",
				children: [
					/* @__PURE__ */ jsx(Target, {}),
					" ",
					task.objective
				]
			}),
			meta && /* @__PURE__ */ jsxs("div", {
				className: `task-kind task-kind--${kind}`,
				children: [
					/* @__PURE__ */ jsx("span", {
						className: "task-kind-icon",
						children: /* @__PURE__ */ jsx(Icon, {})
					}),
					/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: meta.label }), /* @__PURE__ */ jsx("p", { children: meta.blurb })] }),
					task.xp_reward ? /* @__PURE__ */ jsxs("span", {
						className: "task-kind-xp",
						children: [
							/* @__PURE__ */ jsx(Zap, {}),
							" ",
							task.xp_reward,
							" XP"
						]
					}) : null
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "task-primary",
				children: [
					playable && /* @__PURE__ */ jsxs("button", {
						className: "button button--primary task-start",
						onClick: () => setPlaying(true),
						disabled: busy,
						children: [
							task.is_completed ? "Practice again" : meta.cta,
							" ",
							/* @__PURE__ */ jsx(ArrowRight, {})
						]
					}),
					kind === "boss_battle" && /* @__PURE__ */ jsxs("a", {
						className: "button button--primary task-start",
						href: bossLink,
						target: "_blank",
						rel: "noreferrer",
						children: [
							meta.cta,
							" ",
							/* @__PURE__ */ jsx(ArrowRight, {})
						]
					}),
					!playable && kind !== "boss_battle" && /* @__PURE__ */ jsxs("button", {
						className: "button button--primary task-start",
						onClick: complete,
						disabled: busy || task.is_completed,
						children: [
							task.is_completed ? "Completed" : "Mark complete",
							" ",
							/* @__PURE__ */ jsx(Check, {})
						]
					})
				]
			}),
			!task.node_type && task.secondary_content_id && /* @__PURE__ */ jsxs("a", {
				className: "button button--quiet task-legacy-guide",
				href: `/strategy_article/${task.id}`,
				target: "_blank",
				rel: "noreferrer",
				children: [/* @__PURE__ */ jsx(BookOpen, {}), " Strategy guide"]
			}),
			task.reason && /* @__PURE__ */ jsxs("div", {
				className: "task-why",
				children: [/* @__PURE__ */ jsx("small", { children: "WHY THIS STEP" }), /* @__PURE__ */ jsx(Markdown, { children: task.reason })]
			}),
			error && /* @__PURE__ */ jsx("p", {
				className: "form-error",
				children: error
			}),
			/* @__PURE__ */ jsx("button", {
				className: "task-more",
				onClick: () => setDetailsOpen((o) => !o),
				"aria-expanded": detailsOpen,
				children: detailsOpen ? "Hide" : "Notes, target date, and other options"
			}),
			detailsOpen && /* @__PURE__ */ jsxs("div", {
				className: "task-details",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "task-deadline",
						children: [/* @__PURE__ */ jsxs("label", { children: ["Target date", /* @__PURE__ */ jsx("input", {
							type: "date",
							value: dueDate,
							onChange: (e) => setDueDate(e.target.value)
						})] }), /* @__PURE__ */ jsx("button", {
							onClick: saveDeadline,
							children: "Save date"
						})]
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "task-notes",
						children: [
							/* @__PURE__ */ jsx("label", { children: "Notes and sub-steps" }),
							task.subtasks.map((s) => /* @__PURE__ */ jsxs("button", {
								className: s.is_completed ? "checked" : "",
								onClick: () => toggleNote(s),
								disabled: busy,
								children: [/* @__PURE__ */ jsx("span", { children: s.is_completed && /* @__PURE__ */ jsx(Check, {}) }), s.description]
							}, s.id)),
							/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("input", {
								value: note,
								onChange: (e) => setNote(e.target.value),
								onKeyDown: (e) => e.key === "Enter" && addNote(),
								placeholder: "Add a note or smaller step",
								disabled: busy
							}), /* @__PURE__ */ jsx("button", {
								onClick: addNote,
								disabled: busy || !note.trim(),
								"aria-label": "Add note or sub-step",
								children: /* @__PURE__ */ jsx(Plus, {})
							})] })
						]
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "modal-actions",
						children: [(kind === "boss_battle" || !playable) && !task.is_completed && /* @__PURE__ */ jsxs("button", {
							className: "button button--quiet",
							onClick: complete,
							disabled: busy,
							children: ["Mark complete ", /* @__PURE__ */ jsx(Check, {})]
						}), playable && !task.is_skipped && !task.is_completed && /* @__PURE__ */ jsx("button", {
							className: "button button--quiet",
							onClick: skipTask,
							disabled: busy,
							children: "Skip this step"
						})]
					})
				]
			})
		]
	});
}
function AddTask({ category, onClose, onAdded }) {
	const [description, setDescription] = useState("");
	const [date, setDate] = useState("");
	const [error, setError] = useState("");
	const [busy, setBusy] = useState(false);
	const submit = async (e) => {
		e.preventDefault();
		if (busy) return;
		setBusy(true);
		setError("");
		try {
			onAdded((await api("/api/add_task", {
				method: "POST",
				body: JSON.stringify({
					description,
					category,
					due_date: date || null
				})
			})).task);
		} catch (x) {
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	return /* @__PURE__ */ jsxs(Modal, {
		onClose,
		label: "Add a personal step",
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "modal-kicker",
				children: "ADD A PERSONAL STEP"
			}),
			/* @__PURE__ */ jsx("h2", { children: "Make the path yours." }),
			/* @__PURE__ */ jsxs("form", {
				className: "modal-form",
				onSubmit: submit,
				children: [
					/* @__PURE__ */ jsxs("label", { children: ["What do you want to do?", /* @__PURE__ */ jsx("textarea", {
						autoFocus: true,
						value: description,
						onChange: (e) => setDescription(e.target.value),
						placeholder: "Write a clear, finishable action",
						maxLength: 500,
						disabled: busy
					})] }),
					/* @__PURE__ */ jsxs("label", { children: [
						"Due date ",
						/* @__PURE__ */ jsx("span", { children: "optional" }),
						/* @__PURE__ */ jsx("input", {
							type: "date",
							value: date,
							onChange: (e) => setDate(e.target.value),
							disabled: busy
						})
					] }),
					error && /* @__PURE__ */ jsx("p", {
						className: "form-error",
						role: "alert",
						children: error
					}),
					/* @__PURE__ */ jsxs("button", {
						className: "button button--primary",
						disabled: busy || !description.trim(),
						children: [
							busy ? "Adding…" : "Add to path",
							" ",
							/* @__PURE__ */ jsx(ArrowRight, {})
						]
					})
				]
			})
		]
	});
}
var START_HEARTS = 5;
var REFILL_HEARTS = 2;
function PlayerShell({ kicker, progress, hearts, xp, onClose, children }) {
	return createPortal(/* @__PURE__ */ jsx("div", {
		className: "player-wrap",
		role: "dialog",
		"aria-modal": "true",
		children: /* @__PURE__ */ jsxs("div", {
			className: "player",
			children: [/* @__PURE__ */ jsxs("header", {
				className: "player-bar",
				children: [
					/* @__PURE__ */ jsx("button", {
						className: "player-quit",
						onClick: onClose,
						"aria-label": "Leave",
						children: /* @__PURE__ */ jsx(X, {})
					}),
					/* @__PURE__ */ jsx("div", {
						className: "player-progress",
						role: "progressbar",
						"aria-valuenow": Math.round(progress * 100),
						"aria-valuemin": 0,
						"aria-valuemax": 100,
						children: /* @__PURE__ */ jsx("span", { style: { width: `${Math.max(2, Math.round(progress * 100))}%` } })
					}),
					hearts != null && /* @__PURE__ */ jsxs("div", {
						className: `player-hearts ${hearts <= 1 ? "low" : ""}`,
						"aria-label": `${hearts} hearts left`,
						children: [
							/* @__PURE__ */ jsx(Flame, {}),
							" ",
							/* @__PURE__ */ jsx("b", { children: hearts })
						]
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "player-xp",
						"aria-label": `${xp} XP this session`,
						children: [
							/* @__PURE__ */ jsx(Zap, {}),
							" ",
							/* @__PURE__ */ jsx("b", { children: xp })
						]
					})
				]
			}), /* @__PURE__ */ jsxs("div", {
				className: "player-body",
				children: [kicker && /* @__PURE__ */ jsx("div", {
					className: "player-kicker",
					children: kicker
				}), children]
			})]
		})
	}), document.body);
}
function CoachBox({ kind, refId, seed }) {
	const [open, setOpen] = useState(false);
	const [question, setQuestion] = useState("");
	const [reply, setReply] = useState("");
	const [busy, setBusy] = useState(false);
	const ask = async (text) => {
		setBusy(true);
		setReply("");
		try {
			const r = await api("/api/coach", {
				method: "POST",
				body: JSON.stringify({
					kind,
					ref_id: refId,
					message: text
				})
			});
			setReply(r.reply);
		} catch (e) {
			setReply(e.message);
		} finally {
			setBusy(false);
			setQuestion("");
		}
	};
	if (!open) return /* @__PURE__ */ jsxs("button", {
		className: "coach-open",
		onClick: () => {
			setOpen(true);
			if (!reply) ask(seed || "Explain this to me another way.");
		},
		children: [/* @__PURE__ */ jsx(Sparkles, {}), " Ask Mentics about this"]
	});
	return /* @__PURE__ */ jsxs("div", {
		className: "coach-box",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "coach-head",
				children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Sparkles, {}), " Mentics tutor"] }), /* @__PURE__ */ jsx("button", {
					onClick: () => setOpen(false),
					"aria-label": "Close tutor",
					children: /* @__PURE__ */ jsx(X, {})
				})]
			}),
			busy && !reply ? /* @__PURE__ */ jsxs("div", {
				className: "coach-thinking",
				children: [
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("i", {})
				]
			}) : /* @__PURE__ */ jsx(Markdown, { children: reply }),
			/* @__PURE__ */ jsxs("form", {
				onSubmit: (e) => {
					e.preventDefault();
					if (question.trim() && !busy) ask(question.trim());
				},
				children: [/* @__PURE__ */ jsx("input", {
					value: question,
					onChange: (e) => setQuestion(e.target.value),
					placeholder: "Ask a follow-up about this step…",
					maxLength: 600
				}), /* @__PURE__ */ jsx("button", {
					disabled: !question.trim() || busy,
					"aria-label": "Send",
					children: /* @__PURE__ */ jsx(Send, {})
				})]
			})
		]
	});
}
function TeachStep({ step, onNext, isLast }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "teach-step",
		children: [
			/* @__PURE__ */ jsx("h3", { children: step.title }),
			/* @__PURE__ */ jsx(Markdown, { children: step.body }),
			step.worked_example && /* @__PURE__ */ jsxs("div", {
				className: "teach-example",
				children: [/* @__PURE__ */ jsx("small", { children: "WORKED EXAMPLE" }), /* @__PURE__ */ jsx(Markdown, { children: step.worked_example })]
			}),
			step.takeaway && /* @__PURE__ */ jsxs("div", {
				className: "teach-takeaway",
				children: [
					/* @__PURE__ */ jsx(Target, {}),
					" ",
					/* @__PURE__ */ jsx("p", { children: step.takeaway })
				]
			}),
			step.trap && /* @__PURE__ */ jsxs("div", {
				className: "teach-trap",
				children: [
					/* @__PURE__ */ jsx(Hand, {}),
					" ",
					/* @__PURE__ */ jsxs("p", { children: [
						/* @__PURE__ */ jsx("b", { children: "Watch out." }),
						" ",
						step.trap
					] })
				]
			}),
			/* @__PURE__ */ jsx(CoachBox, {
				kind: "lesson_step",
				refId: step.id,
				seed: "Explain this card in a different way, with another example."
			}),
			/* @__PURE__ */ jsx("div", {
				className: "player-actions",
				children: /* @__PURE__ */ jsxs("button", {
					className: "button button--primary player-cta",
					onClick: onNext,
					children: [
						isLast ? "Finish" : "Got it",
						" ",
						/* @__PURE__ */ jsx(ArrowRight, {})
					]
				})
			})
		]
	});
}
function CheckStep({ step, coachKind, feedback, selected, onSelect, onCheck, onContinue, busy, replay }) {
	const letters = [
		"A",
		"B",
		"C",
		"D",
		"E",
		"F"
	];
	return /* @__PURE__ */ jsxs("div", {
		className: `check-step ${feedback ? feedback.is_correct ? "is-right" : "is-wrong" : ""}`,
		children: [
			replay && /* @__PURE__ */ jsxs("div", {
				className: "check-replay",
				children: [/* @__PURE__ */ jsx(RotateCcw, {}), " Second look — you missed this one earlier."]
			}),
			step.source_or_prompt && /* @__PURE__ */ jsxs("div", {
				className: "check-source",
				children: [/* @__PURE__ */ jsx("small", { children: "PASSAGE / SETUP" }), /* @__PURE__ */ jsx(Markdown, { children: step.source_or_prompt })]
			}),
			/* @__PURE__ */ jsx("p", {
				className: "check-question",
				children: step.question_text
			}),
			/* @__PURE__ */ jsx("div", {
				className: "check-options",
				children: (step.options || []).map((option, index) => {
					const state = !feedback ? selected === index ? "picked" : "" : index === feedback.correct_option ? "right" : selected === index ? "wrong" : "";
					return /* @__PURE__ */ jsxs("button", {
						className: `check-option ${state}`,
						disabled: Boolean(feedback) || busy,
						onClick: () => onSelect(index),
						children: [/* @__PURE__ */ jsx("i", { children: letters[index] }), /* @__PURE__ */ jsx("span", { children: option })]
					}, index);
				})
			}),
			feedback && /* @__PURE__ */ jsxs("div", {
				className: "check-feedback",
				children: [
					/* @__PURE__ */ jsx("h4", { children: feedback.is_correct ? "Correct." : "Not quite." }),
					/* @__PURE__ */ jsx(Markdown, { children: feedback.explanation }),
					/* @__PURE__ */ jsx(CoachBox, {
						kind: coachKind,
						refId: step.id,
						seed: "Why is that the right answer? Walk me through it."
					})
				]
			}),
			/* @__PURE__ */ jsx("div", {
				className: "player-actions",
				children: feedback ? /* @__PURE__ */ jsxs("button", {
					className: "button button--primary player-cta",
					onClick: onContinue,
					children: ["Continue ", /* @__PURE__ */ jsx(ArrowRight, {})]
				}) : /* @__PURE__ */ jsx("button", {
					className: "button button--primary player-cta",
					disabled: selected == null || busy,
					onClick: onCheck,
					children: busy ? "Checking…" : "Check"
				})
			})
		]
	});
}
function PlayerDone({ title, correct, total, xp, note, onClose }) {
	const accuracy = total ? Math.round(correct / total * 100) : null;
	return /* @__PURE__ */ jsxs("div", {
		className: "player-done",
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "player-done-mark",
				children: /* @__PURE__ */ jsx(Trophy, {})
			}),
			/* @__PURE__ */ jsx("h2", { children: title }),
			accuracy != null && /* @__PURE__ */ jsxs("p", {
				className: "player-score",
				children: [
					correct,
					" of ",
					total,
					" correct ",
					/* @__PURE__ */ jsxs("span", { children: [accuracy, "%"] })
				]
			}),
			xp > 0 && /* @__PURE__ */ jsxs("div", {
				className: "player-xp-award",
				children: [
					/* @__PURE__ */ jsx(Zap, {}),
					" +",
					xp,
					" XP"
				]
			}),
			note && /* @__PURE__ */ jsx("div", {
				className: "player-recap",
				children: /* @__PURE__ */ jsx(Markdown, { children: note })
			}),
			/* @__PURE__ */ jsxs("button", {
				className: "button button--primary player-cta",
				onClick: onClose,
				children: ["Back to your path ", /* @__PURE__ */ jsx(ArrowRight, {})]
			})
		]
	});
}
function OutOfHearts({ missed, onContinue }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "player-refill",
		children: [
			/* @__PURE__ */ jsx("h2", { children: "Let's reset for a second." }),
			/* @__PURE__ */ jsx("p", { children: "You missed a few. Read these back, then keep going — the questions you missed are still in the queue." }),
			/* @__PURE__ */ jsx("div", {
				className: "refill-list",
				children: missed.map((item, index) => /* @__PURE__ */ jsxs("div", {
					className: "refill-item",
					children: [/* @__PURE__ */ jsx("p", {
						className: "refill-question",
						children: item.question_text
					}), /* @__PURE__ */ jsx(Markdown, { children: item.explanation })]
				}, index))
			}),
			/* @__PURE__ */ jsxs("button", {
				className: "button button--primary player-cta",
				onClick: onContinue,
				children: ["I'm ready ", /* @__PURE__ */ jsx(ArrowRight, {})]
			})
		]
	});
}
function useStepQueue(length) {
	const [queue, setQueue] = useState(() => Array.from({ length }, (_, i) => i));
	const [cursor, setCursor] = useState(0);
	return {
		queue,
		cursor,
		requeue: (index) => setQueue((q) => [...q, index]),
		advance: () => setCursor((c) => c + 1),
		progress: queue.length ? cursor / queue.length : 0,
		done: cursor >= queue.length
	};
}
function useRunState() {
	const [hearts, setHearts] = useState(START_HEARTS);
	const [xp, setXp] = useState(0);
	const [missed, setMissed] = useState([]);
	const [refill, setRefill] = useState(false);
	const [selected, setSelected] = useState(null);
	const [feedback, setFeedback] = useState(null);
	const [busy, setBusy] = useState(false);
	const registerWrong = (item) => {
		setMissed((m) => [...m, item]);
		setHearts((h) => Math.max(0, h - 1));
	};
	const clearStep = () => {
		setSelected(null);
		setFeedback(null);
	};
	return {
		hearts,
		setHearts,
		xp,
		setXp,
		missed,
		refill,
		setRefill,
		selected,
		setSelected,
		feedback,
		setFeedback,
		busy,
		setBusy,
		registerWrong,
		clearStep
	};
}
function PlayerLoading({ onClose }) {
	return /* @__PURE__ */ jsx(PlayerShell, {
		progress: 0,
		xp: 0,
		onClose,
		children: /* @__PURE__ */ jsxs("div", {
			className: "player-loading",
			children: [
				/* @__PURE__ */ jsx("span", { className: "skeleton" }),
				/* @__PURE__ */ jsx("span", { className: "skeleton" }),
				/* @__PURE__ */ jsx("span", { className: "skeleton" })
			]
		})
	});
}
function PlayerError({ title, message, onClose }) {
	return /* @__PURE__ */ jsx(PlayerShell, {
		progress: 0,
		xp: 0,
		onClose,
		children: /* @__PURE__ */ jsxs("div", {
			className: "player-error",
			children: [
				/* @__PURE__ */ jsx("h2", { children: title }),
				/* @__PURE__ */ jsx("p", { children: message }),
				/* @__PURE__ */ jsx("button", {
					className: "button button--primary player-cta",
					onClick: onClose,
					children: "Back to your path"
				})
			]
		})
	});
}
function useContent(url, deps) {
	const [data, setData] = useState(null);
	const [error, setError] = useState("");
	useEffect(() => {
		let live = true;
		api(url).then((d) => {
			if (live) setData(d);
		}).catch((e) => {
			if (live) setError(e.message);
		});
		return () => {
			live = false;
		};
	}, deps);
	return {
		data,
		error
	};
}
function LessonPlayer({ task, onClose, onCompleted }) {
	const { data, error } = useContent(`/api/lesson/${task.id}`, [task.id]);
	if (error) return /* @__PURE__ */ jsx(PlayerError, {
		title: "This lesson could not open.",
		message: error,
		onClose
	});
	if (!data) return /* @__PURE__ */ jsx(PlayerLoading, { onClose });
	return /* @__PURE__ */ jsx(LessonRun, {
		lesson: data,
		task,
		onClose,
		onCompleted
	}, data.lesson_id);
}
function LessonRun({ lesson, task, onClose, onCompleted }) {
	const steps = lesson.steps || [];
	const run = useRunState();
	const [summary, setSummary] = useState(null);
	const { queue, cursor, requeue, advance, progress, done } = useStepQueue(steps.length);
	useEffect(() => {
		if (done) return;
		api(`/api/lesson/${task.id}/progress`, {
			method: "POST",
			body: JSON.stringify({ current_step: cursor })
		}).catch(() => {});
	}, [
		cursor,
		task.id,
		done
	]);
	useEffect(() => {
		if (!done || summary) return;
		let live = true;
		api(`/api/lesson/${task.id}/finish`, {
			method: "POST",
			body: JSON.stringify({})
		}).then((r) => {
			if (live) setSummary(r);
		}).catch((e) => {
			if (live) setSummary({
				correct: 0,
				total: 0,
				xp_earned: 0,
				recap: "",
				error: e.message
			});
		});
		return () => {
			live = false;
		};
	}, [
		done,
		summary,
		task.id
	]);
	if (summary) return /* @__PURE__ */ jsx(PlayerShell, {
		progress: 1,
		hearts: run.hearts,
		xp: run.xp,
		onClose,
		children: /* @__PURE__ */ jsx(PlayerDone, {
			title: "Lesson complete.",
			correct: summary.correct,
			total: summary.total,
			xp: summary.xp_earned || 0,
			note: summary.recap,
			onClose: () => onCompleted(summary)
		})
	});
	if (run.refill) return /* @__PURE__ */ jsx(PlayerShell, {
		progress,
		hearts: run.hearts,
		xp: run.xp,
		onClose,
		children: /* @__PURE__ */ jsx(OutOfHearts, {
			missed: run.missed.slice(-3),
			onContinue: () => {
				run.setHearts(REFILL_HEARTS);
				run.setRefill(false);
			}
		})
	});
	const index = queue[cursor];
	const step = steps[index];
	if (!step) return /* @__PURE__ */ jsx(PlayerLoading, { onClose });
	const checkAnswer = async () => {
		run.setBusy(true);
		try {
			const r = await api(`/api/lesson/${task.id}/answer`, {
				method: "POST",
				body: JSON.stringify({
					step_id: step.id,
					selected_option: run.selected
				})
			});
			run.setFeedback(r);
			if (r.is_correct) run.setXp((x) => x + 5);
			else {
				requeue(index);
				run.registerWrong({
					question_text: step.question_text,
					explanation: r.explanation
				});
			}
		} catch (e) {
			toast.error("Could not check that answer", { description: e.message });
		} finally {
			run.setBusy(false);
		}
	};
	const next = () => {
		const wasWrong = run.feedback && !run.feedback.is_correct;
		run.clearStep();
		advance();
		if (wasWrong && run.hearts <= 1) run.setRefill(true);
	};
	return /* @__PURE__ */ jsxs(PlayerShell, {
		kicker: `${lesson.skill_label || lesson.subject} · Lesson`,
		progress,
		hearts: run.hearts,
		xp: run.xp,
		onClose,
		children: [cursor === 0 && lesson.intro && step.step_type !== "check" && /* @__PURE__ */ jsxs("div", {
			className: "lesson-intro",
			children: [lesson.objective && /* @__PURE__ */ jsxs("span", {
				className: "lesson-objective",
				children: [
					/* @__PURE__ */ jsx(Target, {}),
					" ",
					lesson.objective
				]
			}), /* @__PURE__ */ jsx(Markdown, { children: lesson.intro })]
		}), step.step_type === "check" ? /* @__PURE__ */ jsx(CheckStep, {
			step,
			coachKind: "lesson_step",
			feedback: run.feedback,
			selected: run.selected,
			busy: run.busy,
			replay: cursor >= steps.length,
			onSelect: run.setSelected,
			onCheck: checkAnswer,
			onContinue: next
		}) : /* @__PURE__ */ jsx(TeachStep, {
			step,
			isLast: cursor === queue.length - 1,
			onNext: next
		})]
	});
}
function AssessmentPlayer({ task, onClose, onCompleted }) {
	const kind = task.task_format === "quiz" ? "quiz" : "sprint";
	const { data, error } = useContent(kind === "quiz" ? `/api/quiz/${task.id}` : `/api/practice_sprint/${task.id}`, [task.id, kind]);
	if (error) return /* @__PURE__ */ jsx(PlayerError, {
		title: "This activity could not open.",
		message: error,
		onClose
	});
	if (!data) return /* @__PURE__ */ jsx(PlayerLoading, { onClose });
	return /* @__PURE__ */ jsx(AssessmentRun, {
		data,
		kind,
		task,
		onClose,
		onCompleted
	}, task.id);
}
function AssessmentRun({ data, kind, task, onClose, onCompleted }) {
	const questions = data.questions || [];
	const run = useRunState();
	const [tally, setTally] = useState({
		correct: 0,
		total: 0
	});
	const [summary, setSummary] = useState(null);
	const { queue, cursor, requeue, advance, progress, done } = useStepQueue(questions.length);
	useEffect(() => {
		if (!done || summary) return;
		let live = true;
		api("/api/assessment/finish", {
			method: "POST",
			body: JSON.stringify({ task_id: task.id })
		}).then((r) => {
			if (live) setSummary(r);
		}).catch(() => {
			if (live) setSummary({ xp_earned: 0 });
		});
		return () => {
			live = false;
		};
	}, [
		done,
		summary,
		task.id
	]);
	if (summary) return /* @__PURE__ */ jsx(PlayerShell, {
		progress: 1,
		hearts: run.hearts,
		xp: run.xp,
		onClose,
		children: /* @__PURE__ */ jsx(PlayerDone, {
			title: kind === "quiz" ? "Review complete." : "Practice complete.",
			correct: tally.correct,
			total: tally.total,
			xp: summary.xp_earned || 0,
			note: tally.total && tally.correct / tally.total < .7 ? "That accuracy says this skill needs another pass. Your next path will build on exactly what you missed here." : "Strong run. Mentics logged which sub-skills held up, so the next unit can move you forward.",
			onClose: () => onCompleted(summary)
		})
	});
	if (run.refill) return /* @__PURE__ */ jsx(PlayerShell, {
		progress,
		hearts: run.hearts,
		xp: run.xp,
		onClose,
		children: /* @__PURE__ */ jsx(OutOfHearts, {
			missed: run.missed.slice(-3),
			onContinue: () => {
				run.setHearts(REFILL_HEARTS);
				run.setRefill(false);
			}
		})
	});
	const index = queue[cursor];
	const question = questions[index];
	if (!question) return /* @__PURE__ */ jsx(PlayerLoading, { onClose });
	const checkAnswer = async () => {
		run.setBusy(true);
		try {
			const r = await api("/api/assessment/answer", {
				method: "POST",
				body: JSON.stringify({
					kind,
					question_id: question.id,
					selected_option: run.selected
				})
			});
			run.setFeedback(r);
			setTally((t) => ({
				correct: t.correct + (r.is_correct ? 1 : 0),
				total: t.total + 1
			}));
			if (r.is_correct) run.setXp((x) => x + 5);
			else {
				requeue(index);
				run.registerWrong({
					question_text: question.question_text,
					explanation: r.explanation
				});
			}
		} catch (e) {
			toast.error("Could not check that answer", { description: e.message });
		} finally {
			run.setBusy(false);
		}
	};
	const next = () => {
		const wasWrong = run.feedback && !run.feedback.is_correct;
		run.clearStep();
		advance();
		if (wasWrong && run.hearts <= 1) run.setRefill(true);
	};
	return /* @__PURE__ */ jsx(PlayerShell, {
		kicker: `${data.title} · ${kind === "quiz" ? "Review" : "Practice"}`,
		progress,
		hearts: run.hearts,
		xp: run.xp,
		onClose,
		children: /* @__PURE__ */ jsx(CheckStep, {
			step: question,
			coachKind: kind,
			feedback: run.feedback,
			selected: run.selected,
			busy: run.busy,
			replay: cursor >= questions.length,
			onSelect: run.setSelected,
			onCheck: checkAnswer,
			onContinue: next
		})
	});
}
function EssayCoach({ onClose }) {
	const [prompt, setPrompt] = useState("");
	const [essay, setEssay] = useState("");
	const [feedback, setFeedback] = useState("");
	const [busy, setBusy] = useState(false);
	const analyze = async () => {
		if (essay.trim().length < 50) return;
		setBusy(true);
		try {
			setFeedback((await api("/api/analyze_essay", {
				method: "POST",
				body: JSON.stringify({
					essay_text: essay,
					essay_prompt: prompt || "a general college application essay"
				})
			})).feedback);
		} catch (e) {
			setFeedback(e.message);
		} finally {
			setBusy(false);
		}
	};
	return /* @__PURE__ */ jsxs(Modal, {
		onClose,
		wide: true,
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "modal-kicker",
				children: "MENTICS ESSAY COACH"
			}),
			/* @__PURE__ */ jsx("h2", { children: "Strengthen the essay without losing your voice." }),
			/* @__PURE__ */ jsxs("div", {
				className: "essay-workspace",
				children: [
					/* @__PURE__ */ jsxs("label", { children: ["Essay prompt", /* @__PURE__ */ jsx("input", {
						value: prompt,
						onChange: (e) => setPrompt(e.target.value),
						placeholder: "Common App prompt or supplemental question"
					})] }),
					/* @__PURE__ */ jsxs("label", { children: ["Essay draft", /* @__PURE__ */ jsx("textarea", {
						value: essay,
						onChange: (e) => setEssay(e.target.value),
						rows: "12",
						maxLength: "20000",
						placeholder: "Paste your draft here..."
					})] }),
					/* @__PURE__ */ jsxs("button", {
						className: "button button--primary",
						onClick: analyze,
						disabled: busy || essay.trim().length < 50,
						children: [
							busy ? "Analyzing…" : "Get structured feedback",
							" ",
							/* @__PURE__ */ jsx(Sparkles, {})
						]
					}),
					feedback && /* @__PURE__ */ jsx("div", {
						className: "essay-feedback",
						children: /* @__PURE__ */ jsx(Markdown, { children: feedback })
					})
				]
			})
		]
	});
}
var chatStarters = {
	"Test Prep": [
		{
			icon: Target,
			label: "What should I focus on?"
		},
		{
			icon: Brain,
			label: "Explain my weakest skill"
		},
		{
			icon: RotateCcw,
			label: "Rebuild my path around math"
		},
		{
			icon: CalendarDays,
			label: "Am I on pace for my test date?"
		}
	],
	"College Planning": [
		{
			icon: Target,
			label: "What should I do this month?"
		},
		{
			icon: GraduationCap,
			label: "Is my college list balanced?"
		},
		{
			icon: PenLine,
			label: "Help me start my personal statement"
		},
		{
			icon: RotateCcw,
			label: "Rebuild my path around applications"
		}
	]
};
function ChatPanel({ open, onClose, category, onNewPath }) {
	const [messages, setMessages] = useState([]);
	const [input, setInput] = useState("");
	const [busy, setBusy] = useState(false);
	const [historyError, setHistoryError] = useState("");
	const scroller = useRef(null);
	const composer = useRef(null);
	const starters = chatStarters[category] || chatStarters["Test Prep"];
	const conversationStarted = messages.some((m) => m.role === "user");
	useEffect(() => {
		if (open && messages.length === 0) api(`/api/chat_history?category=${encodeURIComponent(category)}`).then((h) => setMessages(Array.isArray(h) && h.length ? h : [{
			role: "assistant",
			content: `I'm here with your ${category.toLowerCase()} path. Ask about any step, concept, or roadblock — I can see exactly where you are.`
		}])).catch(() => {
			setHistoryError("I could not restore the earlier conversation, but you can start a new one here.");
			setMessages([{
				role: "assistant",
				content: `I'm ready to help with your ${category.toLowerCase()} path.`
			}]);
		});
	}, [
		open,
		category,
		messages.length
	]);
	useEffect(() => {
		const node = scroller.current;
		if (node) node.scrollTo({
			top: node.scrollHeight,
			behavior: "smooth"
		});
	}, [messages, busy]);
	useEffect(() => {
		const node = composer.current;
		if (!node) return;
		node.style.height = "auto";
		node.style.height = `${Math.min(node.scrollHeight, 140)}px`;
	}, [input]);
	const ask = async (text) => {
		if (!text.trim() || busy) return;
		const next = [...messages, {
			role: "user",
			content: text.trim()
		}];
		setMessages(next);
		setInput("");
		setBusy(true);
		try {
			const r = await api(`/api/chat?category=${encodeURIComponent(category)}`, {
				method: "POST",
				body: JSON.stringify({ history: next })
			});
			if (Object.prototype.hasOwnProperty.call(r, "new_path")) {
				if (!Array.isArray(r.new_path) || r.new_path.length !== 5) throw new Error("Mentics could not build a complete five-step path. Your current path is unchanged.");
				onNewPath(r.new_path);
				setMessages([...next, {
					role: "assistant",
					content: r.reply || "Your new path is ready. I used our conversation to shape it."
				}]);
			} else setMessages([...next, {
				role: "assistant",
				content: r.reply
			}]);
		} catch (x) {
			setMessages([...next, {
				role: "assistant",
				content: x.message
			}]);
		} finally {
			setBusy(false);
		}
	};
	const send = (e) => {
		e.preventDefault();
		ask(input);
	};
	const reset = async () => {
		try {
			await api("/api/reset_chat", {
				method: "POST",
				body: JSON.stringify({ category })
			});
			setHistoryError("");
			setMessages([{
				role: "assistant",
				content: `Fresh start. What would you like help with on your ${category.toLowerCase()} path?`
			}]);
		} catch (error) {
			setHistoryError(error.message);
		}
	};
	return /* @__PURE__ */ jsxs("aside", {
		className: `chat-panel ${open ? "chat-panel--open" : ""}`,
		"aria-hidden": !open,
		inert: !open || void 0,
		children: [
			/* @__PURE__ */ jsxs("header", {
				className: "chat-head",
				children: [/* @__PURE__ */ jsxs("span", {
					className: "chat-identity",
					children: [/* @__PURE__ */ jsx("span", {
						className: "chat-wordmark",
						children: "MENTICS"
					}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "Path guide" }), /* @__PURE__ */ jsxs("small", { children: [
						/* @__PURE__ */ jsx("em", { className: "chat-live" }),
						" Here with your ",
						category.toLowerCase(),
						" path"
					] })] })]
				}), /* @__PURE__ */ jsxs("div", {
					className: "chat-head-actions",
					children: [/* @__PURE__ */ jsx("button", {
						onClick: reset,
						"aria-label": "Start a new conversation",
						title: "New conversation",
						children: /* @__PURE__ */ jsx(RotateCcw, {})
					}), /* @__PURE__ */ jsx("button", {
						onClick: onClose,
						"aria-label": "Close chat",
						title: "Close",
						children: /* @__PURE__ */ jsx(X, {})
					})]
				})]
			}),
			historyError && /* @__PURE__ */ jsx("div", {
				className: "chat-notice",
				role: "status",
				children: historyError
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "chat-messages",
				ref: scroller,
				children: [
					messages.map((m, i) => /* @__PURE__ */ jsxs("div", {
						className: `chat-message chat-message--${m.role}`,
						children: [m.role === "assistant" && /* @__PURE__ */ jsx("i", {
							className: "chat-avatar",
							"aria-hidden": "true",
							children: "M"
						}), /* @__PURE__ */ jsx("div", {
							className: "chat-bubble",
							children: m.role === "assistant" ? /* @__PURE__ */ jsx(Markdown, { children: m.content }) : m.content
						})]
					}, i)),
					busy && /* @__PURE__ */ jsxs("div", {
						className: "chat-message chat-message--assistant",
						children: [/* @__PURE__ */ jsx("i", {
							className: "chat-avatar",
							"aria-hidden": "true",
							children: "M"
						}), /* @__PURE__ */ jsxs("div", {
							className: "chat-bubble chat-bubble--thinking",
							children: [
								/* @__PURE__ */ jsx("span", {}),
								/* @__PURE__ */ jsx("span", {}),
								/* @__PURE__ */ jsx("span", {})
							]
						})]
					}),
					!conversationStarted && !busy && /* @__PURE__ */ jsxs("div", {
						className: "chat-starters",
						children: [/* @__PURE__ */ jsx("small", { children: "TRY ASKING" }), starters.map(({ label }) => /* @__PURE__ */ jsxs("button", {
							onClick: () => ask(label),
							children: [/* @__PURE__ */ jsx("span", {
								"aria-hidden": "true",
								children: "→"
							}), label]
						}, label))]
					})
				]
			}),
			/* @__PURE__ */ jsxs("form", {
				className: "chat-composer",
				onSubmit: send,
				children: [/* @__PURE__ */ jsxs("div", {
					className: "chat-composer-field",
					children: [/* @__PURE__ */ jsx("textarea", {
						ref: composer,
						name: "message",
						"aria-label": `Ask Mentics about your ${category.toLowerCase()} path`,
						value: input,
						onChange: (e) => setInput(e.target.value),
						onKeyDown: (e) => {
							if (e.key === "Enter" && !e.shiftKey) {
								e.preventDefault();
								send(e);
							}
						},
						placeholder: "Ask about your path…",
						rows: 1,
						maxLength: 4e3
					}), /* @__PURE__ */ jsx("button", {
						disabled: !input.trim() || busy,
						"aria-label": "Send message",
						children: /* @__PURE__ */ jsx(Send, {})
					})]
				}), /* @__PURE__ */ jsx("p", { children: "Mentics can make mistakes. Check important information." })]
			})
		]
	});
}
function PageIntro({ kicker, title, copy, actions }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "page-intro page-intro--color",
		children: [/* @__PURE__ */ jsxs("div", { children: [
			/* @__PURE__ */ jsxs("div", {
				className: "eyebrow",
				children: [
					/* @__PURE__ */ jsx("span", {}),
					" ",
					kicker
				]
			}),
			/* @__PURE__ */ jsx("h1", { children: title }),
			copy && /* @__PURE__ */ jsx("p", { children: copy })
		] }), actions && /* @__PURE__ */ jsx("div", {
			className: "page-actions",
			children: actions
		})]
	});
}
function AuthPage({ mode }) {
	const signup = mode === "signup";
	return /* @__PURE__ */ jsxs("div", {
		className: "auth-page",
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "auth-brand",
				children: /* @__PURE__ */ jsx(Brand, {})
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "auth-art",
				children: [
					/* @__PURE__ */ jsx("span", { className: "shape shape--peach" }),
					/* @__PURE__ */ jsx("span", { className: "shape shape--mint" }),
					/* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsx("small", { children: "YOUR NEXT CHAPTER" }),
						/* @__PURE__ */ jsx("h1", { children: "Ambition feels better with a plan." }),
						/* @__PURE__ */ jsx("p", { children: "Build momentum across test prep, college planning, and every goal between." })
					] })
				]
			}),
			/* @__PURE__ */ jsxs("main", {
				className: "auth-panel",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "auth-copy",
						children: [
							/* @__PURE__ */ jsx("small", { children: signup ? "START YOUR PATH" : "WELCOME BACK" }),
							/* @__PURE__ */ jsx("h2", { children: signup ? "Join Mentics." : "Continue building." }),
							/* @__PURE__ */ jsx("p", { children: signup ? "Your focused workspace is a minute away." : "Your goals and progress are waiting." })
						]
					}),
					boot.data.error && /* @__PURE__ */ jsx("div", {
						className: "form-error",
						role: "alert",
						children: boot.data.error
					}),
					/* @__PURE__ */ jsxs("form", {
						method: "POST",
						className: "react-form",
						children: [
							/* @__PURE__ */ jsx(CsrfField, {}),
							signup && /* @__PURE__ */ jsxs("label", { children: ["Full name", /* @__PURE__ */ jsx("input", {
								name: "name",
								autoComplete: "name",
								required: true,
								maxLength: "100",
								placeholder: "Your name"
							})] }),
							/* @__PURE__ */ jsxs("label", { children: ["Email address", /* @__PURE__ */ jsx("input", {
								type: "email",
								name: "email",
								autoComplete: "email",
								required: true,
								placeholder: "you@example.com"
							})] }),
							/* @__PURE__ */ jsxs("label", { children: ["Password", /* @__PURE__ */ jsx("input", {
								type: "password",
								name: "password",
								autoComplete: signup ? "new-password" : "current-password",
								minLength: signup ? 8 : void 0,
								maxLength: "128",
								required: true,
								placeholder: signup ? "At least 8 characters" : "Your password"
							})] }),
							signup && /* @__PURE__ */ jsxs("label", {
								className: "legal-consent",
								children: [
									/* @__PURE__ */ jsx("input", {
										type: "checkbox",
										name: "legal_acceptance",
										value: "accepted",
										required: true
									}),
									" ",
									/* @__PURE__ */ jsxs("span", { children: [
										"I agree to the ",
										/* @__PURE__ */ jsx("a", {
											href: "/terms",
											target: "_blank",
											rel: "noreferrer",
											children: "Terms of Service"
										}),
										" and ",
										/* @__PURE__ */ jsx("a", {
											href: "/privacy",
											target: "_blank",
											rel: "noreferrer",
											children: "Privacy Policy"
										}),
										"."
									] })
								]
							}),
							/* @__PURE__ */ jsxs("button", {
								className: "button button--primary",
								type: "submit",
								children: [
									signup ? "Create my account" : "Sign in",
									" ",
									/* @__PURE__ */ jsx(ArrowRight, {})
								]
							})
						]
					}),
					/* @__PURE__ */ jsx("div", {
						className: "form-divider",
						children: /* @__PURE__ */ jsx("span", { children: "or" })
					}),
					/* @__PURE__ */ jsxs("a", {
						className: "google-button",
						href: "/google-login",
						children: [/* @__PURE__ */ jsx("span", { children: "G" }), " Continue with Google"]
					}),
					/* @__PURE__ */ jsxs("p", {
						className: "oauth-legal-notice",
						children: [
							"By continuing with Google, you agree to the ",
							/* @__PURE__ */ jsx("a", {
								href: "/terms",
								target: "_blank",
								rel: "noreferrer",
								children: "Terms of Service"
							}),
							" and acknowledge the ",
							/* @__PURE__ */ jsx("a", {
								href: "/privacy",
								target: "_blank",
								rel: "noreferrer",
								children: "Privacy Policy"
							}),
							"."
						]
					}),
					/* @__PURE__ */ jsxs("p", {
						className: "auth-switch",
						children: [
							signup ? "Already have an account?" : "New to Mentics?",
							" ",
							/* @__PURE__ */ jsx("a", {
								href: signup ? "/login" : "/signup",
								children: signup ? "Sign in" : "Create an account"
							})
						]
					})
				]
			})
		]
	});
}
var learningOptions = [
	[
		"visual",
		"Visual",
		Sparkles,
		"I learn by seeing"
	],
	[
		"auditory",
		"Auditory",
		Headphones,
		"I learn by hearing"
	],
	[
		"reading_writing",
		"Reading / writing",
		PenLine,
		"I learn through words"
	],
	[
		"kinesthetic",
		"Hands-on",
		Hand,
		"I learn by doing"
	]
];
function Onboarding() {
	const [step, setStep] = useState(0);
	const [goal, setGoal] = useState("");
	const [style, setStyle] = useState("");
	const [anxieties, setAnxieties] = useState("");
	const allowSubmit = useRef(false);
	const canNext = step === 0 ? goal : style;
	const submitOnlyFromButton = (event) => {
		if (!allowSubmit.current) {
			event.preventDefault();
			return;
		}
		allowSubmit.current = false;
	};
	const finishOnboarding = (event) => {
		const form = event.currentTarget.form;
		if (!form?.reportValidity()) return;
		allowSubmit.current = true;
		form.requestSubmit();
	};
	return /* @__PURE__ */ jsxs("div", {
		className: "onboarding-page",
		children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsx(Brand, {}), /* @__PURE__ */ jsxs("span", { children: [
			"Step ",
			step + 1,
			" of 3"
		] })] }), /* @__PURE__ */ jsxs("main", { children: [
			/* @__PURE__ */ jsx("div", {
				className: "onboarding-progress",
				children: /* @__PURE__ */ jsx("i", { style: { width: `${(step + 1) / 3 * 100}%` } })
			}),
			boot.data.error && /* @__PURE__ */ jsx("div", {
				className: "form-error",
				children: boot.data.error
			}),
			/* @__PURE__ */ jsxs("form", {
				method: "POST",
				onSubmit: submitOnlyFromButton,
				children: [
					/* @__PURE__ */ jsxs("section", {
						className: step === 0 ? "active" : "",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " START WITH DIRECTION"]
							}),
							/* @__PURE__ */ jsx("h1", { children: "What are we building toward?" }),
							/* @__PURE__ */ jsx("p", { children: "This sets the first version of your Mentics workspace." }),
							/* @__PURE__ */ jsx("div", {
								className: "choice-grid choice-grid--two",
								children: [[
									"test_prep",
									"Test preparation",
									BookOpen,
									"Build confidence for the SAT or ACT"
								], [
									"college_planning",
									"College planning",
									GraduationCap,
									"Turn applications into a clear process"
								]].map(([value, label, Icon, copy]) => /* @__PURE__ */ jsxs("label", {
									className: goal === value ? "selected" : "",
									children: [
										/* @__PURE__ */ jsx("input", {
											type: "radio",
											name: "goal",
											value,
											required: true,
											checked: goal === value,
											onChange: () => setGoal(value)
										}),
										/* @__PURE__ */ jsx(Icon, {}),
										/* @__PURE__ */ jsx("b", { children: label }),
										/* @__PURE__ */ jsx("small", { children: copy })
									]
								}, value))
							})
						]
					}),
					/* @__PURE__ */ jsxs("section", {
						className: step === 1 ? "active" : "",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " MAKE IT YOURS"]
							}),
							/* @__PURE__ */ jsx("h1", { children: "How do you learn best?" }),
							/* @__PURE__ */ jsx("p", { children: "Your tasks and explanations will use this preference." }),
							/* @__PURE__ */ jsx("div", {
								className: "choice-grid",
								children: learningOptions.map(([value, label, Icon, copy]) => /* @__PURE__ */ jsxs("label", {
									className: style === value ? "selected" : "",
									children: [
										/* @__PURE__ */ jsx("input", {
											type: "radio",
											name: "learning_style",
											value,
											required: true,
											checked: style === value,
											onChange: () => setStyle(value)
										}),
										/* @__PURE__ */ jsx(Icon, {}),
										/* @__PURE__ */ jsx("b", { children: label }),
										/* @__PURE__ */ jsx("small", { children: copy })
									]
								}, value))
							})
						]
					}),
					/* @__PURE__ */ jsxs("section", {
						className: step === 2 ? "active" : "",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "eyebrow",
								children: [/* @__PURE__ */ jsx("span", {}), " ONE LAST THING"]
							}),
							/* @__PURE__ */ jsx("h1", { children: "What feels hardest right now?" }),
							/* @__PURE__ */ jsx("p", { children: "Be honest. This helps Mentics meet you where you are." }),
							/* @__PURE__ */ jsx("textarea", {
								name: "anxieties",
								rows: "6",
								value: anxieties,
								onChange: (event) => setAnxieties(event.target.value),
								onKeyDown: (event) => event.stopPropagation(),
								placeholder: "Time management, test anxiety, essays, choosing schools..."
							})
						]
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "onboarding-actions",
						children: [step > 0 ? /* @__PURE__ */ jsxs("button", {
							type: "button",
							className: "button button--quiet",
							onClick: () => setStep(step - 1),
							children: [/* @__PURE__ */ jsx(ArrowLeft, {}), " Back"]
						}) : /* @__PURE__ */ jsx("span", {}), step < 2 ? /* @__PURE__ */ jsxs("button", {
							type: "button",
							className: "button button--primary",
							disabled: !canNext,
							onClick: () => setStep(step + 1),
							children: ["Continue ", /* @__PURE__ */ jsx(ArrowRight, {})]
						}) : /* @__PURE__ */ jsxs("button", {
							type: "button",
							className: "button button--primary",
							onClick: finishOnboarding,
							children: ["Build my workspace ", /* @__PURE__ */ jsx(ArrowRight, {})]
						})]
					})
				]
			})
		] })]
	});
}
function niceScale(min, max) {
	if (!Number.isFinite(min) || !Number.isFinite(max)) return {
		lo: 0,
		hi: 1,
		ticks: [0, 1]
	};
	if (min === max) {
		const pad = Math.max(1, Math.abs(min) * .1);
		min -= pad;
		max += pad;
	}
	const span = max - min;
	const step = Math.pow(10, Math.floor(Math.log10(span / 4)));
	const norm = span / 4 / step;
	const nice = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * step;
	const lo = Math.floor(min / nice) * nice;
	const hi = Math.ceil(max / nice) * nice;
	const ticks = [];
	for (let v = lo; v <= hi + nice / 2; v += nice) ticks.push(Math.round(v * 100) / 100);
	return {
		lo,
		hi,
		ticks
	};
}
function TrendChart({ records = [], label, height = 230 }) {
	const [hover, setHover] = useState(null);
	const wrap = useRef(null);
	const points = records.map((r) => ({
		date: String(r.date),
		value: Number(r.value)
	})).filter((p) => Number.isFinite(p.value));
	if (points.length === 0) return /* @__PURE__ */ jsxs("div", {
		className: "chart-empty",
		children: [/* @__PURE__ */ jsx(BarChart3, {}), /* @__PURE__ */ jsx("p", { children: "No data logged yet. Finish a boss battle or update your scores and this fills in." })]
	});
	const W = 720, H = height, padL = 46, padT = 16, padB = 30;
	const values = points.map((p) => p.value);
	const { lo, hi, ticks } = niceScale(Math.min(...values), Math.max(...values));
	const x = (i) => padL + (points.length === 1 ? 328 : i * 656 / (points.length - 1));
	const y = (v) => padT + (H - padT - padB) * (1 - (v - lo) / (hi - lo || 1));
	const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
	const area = `${line} L${x(points.length - 1).toFixed(1)},${H - padB} L${x(0).toFixed(1)},${H - padB} Z`;
	const last = points[points.length - 1];
	const first = points[0];
	const change = points.length > 1 ? last.value - first.value : null;
	const onMove = (e) => {
		const box = wrap.current?.getBoundingClientRect();
		if (!box) return;
		const px = (e.clientX - box.left) / box.width * W;
		let best = 0;
		points.forEach((_, i) => {
			if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i;
		});
		setHover(best);
	};
	return /* @__PURE__ */ jsxs("div", {
		className: "chart",
		ref: wrap,
		onMouseMove: onMove,
		onMouseLeave: () => setHover(null),
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "chart-head",
				children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: label }), /* @__PURE__ */ jsx("strong", { children: last.value.toLocaleString() })] }), change != null && change !== 0 && /* @__PURE__ */ jsxs("span", {
					className: `chart-change ${change > 0 ? "up" : "down"}`,
					children: [
						change > 0 ? "▲" : "▼",
						" ",
						Math.abs(Math.round(change * 100) / 100),
						" since ",
						first.date.slice(5)
					]
				})]
			}),
			/* @__PURE__ */ jsxs("svg", {
				viewBox: `0 0 ${W} ${H}`,
				role: "img",
				"aria-label": `${label} over time, currently ${last.value}`,
				preserveAspectRatio: "none",
				className: "chart-svg",
				children: [
					/* @__PURE__ */ jsx("defs", { children: /* @__PURE__ */ jsxs("linearGradient", {
						id: "chart-fill",
						x1: "0",
						y1: "0",
						x2: "0",
						y2: "1",
						children: [/* @__PURE__ */ jsx("stop", {
							offset: "0",
							stopColor: "var(--viz-series-1)",
							stopOpacity: ".18"
						}), /* @__PURE__ */ jsx("stop", {
							offset: "1",
							stopColor: "var(--viz-series-1)",
							stopOpacity: "0"
						})]
					}) }),
					ticks.map((t) => /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("line", {
						className: "chart-grid",
						x1: padL,
						x2: 702,
						y1: y(t),
						y2: y(t)
					}), /* @__PURE__ */ jsx("text", {
						className: "chart-tick",
						x: 38,
						y: y(t),
						textAnchor: "end",
						dominantBaseline: "middle",
						children: t
					})] }, t)),
					points.length > 1 && /* @__PURE__ */ jsx("path", {
						d: area,
						fill: "url(#chart-fill)"
					}),
					/* @__PURE__ */ jsx("path", {
						d: line,
						className: "chart-line"
					}),
					points.map((p, i) => (i === points.length - 1 || i === hover || points.length <= 8) && /* @__PURE__ */ jsx("circle", {
						cx: x(i),
						cy: y(p.value),
						r: i === hover ? 6 : 4.5,
						className: `chart-dot ${i === hover ? "active" : ""}`
					}, i)),
					hover != null && /* @__PURE__ */ jsx("line", {
						className: "chart-crosshair",
						x1: x(hover),
						x2: x(hover),
						y1: padT,
						y2: H - padB
					}),
					points.map((p, i) => (i === 0 || i === points.length - 1) && /* @__PURE__ */ jsx("text", {
						className: "chart-tick",
						x: x(i),
						y: H - 10,
						textAnchor: i === 0 ? "start" : "end",
						children: p.date.slice(5)
					}, `d${i}`))
				]
			}),
			hover != null && /* @__PURE__ */ jsxs("div", {
				className: "chart-tip",
				style: { left: `${x(hover) / W * 100}%` },
				children: [/* @__PURE__ */ jsx("b", { children: points[hover].value.toLocaleString() }), /* @__PURE__ */ jsx("small", { children: points[hover].date })]
			})
		]
	});
}
function MasteryRow({ skill, subject, accuracy, attempts, level }) {
	return /* @__PURE__ */ jsxs("li", {
		className: `mastery-row mastery-row--${accuracy >= 85 ? "strong" : accuracy >= 65 ? "fair" : "weak"}`,
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "mastery-label",
				children: [/* @__PURE__ */ jsx("b", { children: skill }), /* @__PURE__ */ jsxs("small", { children: [
					subject,
					" · ",
					attempts,
					" question",
					attempts === 1 ? "" : "s"
				] })]
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mastery-track",
				children: /* @__PURE__ */ jsx("i", { style: { width: `${Math.max(4, accuracy)}%` } })
			}),
			/* @__PURE__ */ jsxs("span", {
				className: "mastery-value",
				children: [accuracy, "%"]
			}),
			/* @__PURE__ */ jsxs("span", {
				className: "mastery-level",
				title: `Mastery level ${level} of 5`,
				children: ["●".repeat(level), "○".repeat(5 - level)]
			})
		]
	});
}
function PathProgressCard({ title, snapshot, href, accent }) {
	if (!snapshot) return /* @__PURE__ */ jsxs("article", {
		className: `path-card path-card--${accent} path-card--empty`,
		children: [
			/* @__PURE__ */ jsx("h3", { children: title }),
			/* @__PURE__ */ jsx("p", { children: "No path yet." }),
			/* @__PURE__ */ jsxs("a", {
				className: "button button--quiet",
				href,
				children: ["Build one ", /* @__PURE__ */ jsx(ArrowRight, {})]
			})
		]
	});
	const pct = snapshot.total ? Math.round(snapshot.completed / snapshot.total * 100) : 0;
	return /* @__PURE__ */ jsxs("article", {
		className: `path-card path-card--${accent}`,
		children: [
			/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsx("h3", { children: title }), /* @__PURE__ */ jsxs("span", { children: [
				snapshot.completed,
				"/",
				snapshot.total
			] })] }),
			snapshot.unitTitle && /* @__PURE__ */ jsx("p", {
				className: "path-card-unit",
				children: snapshot.unitTitle
			}),
			/* @__PURE__ */ jsx("div", {
				className: "path-card-track",
				children: /* @__PURE__ */ jsx("i", { style: { width: `${pct}%` } })
			}),
			/* @__PURE__ */ jsx("ol", {
				className: "path-card-steps",
				children: snapshot.steps.map((s) => /* @__PURE__ */ jsxs("li", {
					className: s.done ? "done" : s.order === snapshot.currentStep ? "current" : "",
					children: [/* @__PURE__ */ jsx("i", { children: s.done ? /* @__PURE__ */ jsx(Check, {}) : s.order }), /* @__PURE__ */ jsx("span", { children: s.skill || s.nodeType || `Step ${s.order}` })]
				}, s.order))
			}),
			/* @__PURE__ */ jsxs("a", {
				className: "button button--quiet",
				href,
				children: [
					snapshot.currentStep ? "Continue" : "Open path",
					" ",
					/* @__PURE__ */ jsx(ArrowRight, {})
				]
			})
		]
	});
}
function GoalMeter({ label, current, goal, min }) {
	if (!current) return null;
	const pct = goal && goal > min ? Math.min(100, Math.round((current - min) / (goal - min) * 100)) : null;
	return /* @__PURE__ */ jsxs("div", {
		className: "goal-meter",
		children: [/* @__PURE__ */ jsxs("div", { children: [
			/* @__PURE__ */ jsx("small", { children: label }),
			/* @__PURE__ */ jsx("strong", { children: current }),
			goal ? /* @__PURE__ */ jsxs("em", { children: ["goal ", goal] }) : null
		] }), pct != null && /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("div", {
			className: "goal-track",
			children: /* @__PURE__ */ jsx("i", { style: { width: `${pct}%` } })
		}), /* @__PURE__ */ jsx("span", {
			className: "goal-caption",
			children: pct >= 100 ? "Goal reached" : `${goal - current} points to go`
		})] })]
	});
}
function StatsPage() {
	const d = boot.data;
	const p = d.practice || {};
	const hasMastery = (d.weakest?.length || 0) > 0;
	const score = (value) => value ?? "—";
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main",
			children: [
				/* @__PURE__ */ jsx(PageIntro, {
					kicker: "ACADEMIC PROFILE",
					title: "Your progress, at a glance.",
					copy: "Your latest test scores, skill evidence, and next steps—kept in one clear view.",
					actions: /* @__PURE__ */ jsxs("a", {
						className: "button button--primary",
						href: "/dashboard/stats/edit",
						children: ["Update scores ", /* @__PURE__ */ jsx(ArrowRight, {})]
					})
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "score-overview",
					"aria-label": "Latest academic scores",
					children: [
						/* @__PURE__ */ jsxs("article", {
							className: "score-card score-card--sat",
							children: [/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsx("small", { children: "LATEST SAT" }),
								/* @__PURE__ */ jsx("strong", { children: score(d.satTotal) }),
								/* @__PURE__ */ jsx("p", { children: d.satEbrw || d.satMath ? `R&W ${score(d.satEbrw)} · Math ${score(d.satMath)}` : "Add your section scores" })
							] }), /* @__PURE__ */ jsx("span", { children: "/ 1600" })]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "score-card score-card--act",
							children: [/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsx("small", { children: "ACT COMPOSITE" }),
								/* @__PURE__ */ jsx("strong", { children: score(d.actComposite || d.actAverage) }),
								/* @__PURE__ */ jsx("p", { children: d.actMath || d.actReading || d.actScience ? `Math ${score(d.actMath)} · Reading ${score(d.actReading)} · Science ${score(d.actScience)}` : "Add your section scores" })
							] }), /* @__PURE__ */ jsx("span", { children: "/ 36" })]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "score-card score-card--gpa",
							children: [/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsx("small", { children: "CURRENT GPA" }),
								/* @__PURE__ */ jsx("strong", { children: score(d.gpa) }),
								/* @__PURE__ */ jsx("p", { children: "Your academic foundation" })
							] }), /* @__PURE__ */ jsx("span", { children: "PROFILE" })]
						})
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "stat-tiles",
					children: [
						/* @__PURE__ */ jsxs("article", {
							className: "stat-tile stat-tile--accent",
							children: [
								/* @__PURE__ */ jsx("small", { children: "TOTAL XP" }),
								/* @__PURE__ */ jsx("strong", { children: d.points.toLocaleString() }),
								/* @__PURE__ */ jsx("p", { children: "Earned from completed steps" })
							]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "stat-tile",
							children: [
								/* @__PURE__ */ jsx("small", { children: "DAY STREAK" }),
								/* @__PURE__ */ jsxs("strong", { children: [d.streak, /* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx(Flame, {}) })] }),
								/* @__PURE__ */ jsx("p", { children: d.streak > 0 ? "Keep it alive today" : "Finish a step to start one" })
							]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "stat-tile",
							children: [
								/* @__PURE__ */ jsx("small", { children: "QUESTIONS ANSWERED" }),
								/* @__PURE__ */ jsx("strong", { children: p.answered || 0 }),
								/* @__PURE__ */ jsx("p", { children: p.accuracy != null ? `${p.accuracy}% correct overall` : "Across lessons and practice" })
							]
						}),
						/* @__PURE__ */ jsxs("article", {
							className: "stat-tile",
							children: [
								/* @__PURE__ */ jsx("small", { children: "TEST DATE" }),
								/* @__PURE__ */ jsx("strong", { children: d.testDate ? (/* @__PURE__ */ new Date(`${d.testDate}T00:00:00`)).toLocaleDateString(void 0, {
									month: "short",
									day: "numeric"
								}) : "—" }),
								/* @__PURE__ */ jsx("p", { children: d.testDate ? "Your next scheduled test" : "Set one in your test path" })
							]
						})
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "stat-columns",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "stat-col",
						children: [
							/* @__PURE__ */ jsx("h2", {
								className: "section-title",
								children: "Where you stand"
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "goal-grid",
								children: [/* @__PURE__ */ jsx(GoalMeter, {
									label: "SAT total",
									current: d.satTotal,
									goal: d.goalSat,
									min: 400
								}), /* @__PURE__ */ jsx(GoalMeter, {
									label: "ACT composite",
									current: d.actAverage,
									goal: d.goalAct,
									min: 1
								})]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "section-scores",
								children: [
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "SAT Reading & Writing" }), /* @__PURE__ */ jsx("b", { children: score(d.satEbrw) })] }),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "SAT Math" }), /* @__PURE__ */ jsx("b", { children: score(d.satMath) })] }),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "ACT Math" }), /* @__PURE__ */ jsx("b", { children: score(d.actMath) })] }),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "ACT Reading" }), /* @__PURE__ */ jsx("b", { children: score(d.actReading) })] }),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "ACT Science" }), /* @__PURE__ */ jsx("b", { children: score(d.actScience) })] })
								]
							}),
							/* @__PURE__ */ jsx("h2", {
								className: "section-title",
								children: "Skill mastery"
							}),
							hasMastery ? /* @__PURE__ */ jsxs(Fragment, { children: [
								/* @__PURE__ */ jsx("p", {
									className: "section-note",
									children: "Measured from every question you have answered in Mentics. Your next path is built from the bottom of this list."
								}),
								/* @__PURE__ */ jsx("ul", {
									className: "mastery-list",
									children: d.weakest.map((m) => /* @__PURE__ */ jsx(MasteryRow, { ...m }, m.skill))
								}),
								d.strongest?.length > 0 && /* @__PURE__ */ jsxs("details", {
									className: "mastery-more",
									children: [/* @__PURE__ */ jsx("summary", { children: "Your strongest skills" }), /* @__PURE__ */ jsx("ul", {
										className: "mastery-list",
										children: d.strongest.map((m) => /* @__PURE__ */ jsx(MasteryRow, { ...m }, m.skill))
									})]
								}),
								d.openMistakes > 0 && /* @__PURE__ */ jsxs("p", {
									className: "section-note section-note--flag",
									children: [
										/* @__PURE__ */ jsx(Target, {}),
										" ",
										d.openMistakes,
										" missed question",
										d.openMistakes === 1 ? "" : "s",
										" are queued for your next unit to teach against."
									]
								})
							] }) : /* @__PURE__ */ jsxs("div", {
								className: "chart-empty",
								children: [/* @__PURE__ */ jsx(Brain, {}), /* @__PURE__ */ jsx("p", { children: "Finish a lesson or practice step and your per-skill mastery appears here." })]
							}),
							d.subjects?.length > 0 && /* @__PURE__ */ jsx("div", {
								className: "subject-split",
								children: d.subjects.map((s) => /* @__PURE__ */ jsxs("div", { children: [
									/* @__PURE__ */ jsx("small", { children: s.subject }),
									/* @__PURE__ */ jsx("div", {
										className: "mastery-track",
										children: /* @__PURE__ */ jsx("i", { style: { width: `${Math.max(4, s.accuracy)}%` } })
									}),
									/* @__PURE__ */ jsxs("b", { children: [s.accuracy, "%"] })
								] }, s.subject))
							})
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "stat-col",
						children: [
							/* @__PURE__ */ jsx("h2", {
								className: "section-title",
								children: "Your paths"
							}),
							/* @__PURE__ */ jsx(PathProgressCard, {
								title: "Test Prep",
								snapshot: d.testPath,
								href: "/dashboard/test-path-view",
								accent: "violet"
							}),
							/* @__PURE__ */ jsx(PathProgressCard, {
								title: "College Planning",
								snapshot: d.collegePath,
								href: "/dashboard/college-path-view",
								accent: "teal"
							}),
							/* @__PURE__ */ jsx("h2", {
								className: "section-title",
								children: "Application progress"
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "app-progress",
								children: [
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "Colleges researched" }), /* @__PURE__ */ jsx("b", { children: d.collegesResearched })] }),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "Applications submitted" }), /* @__PURE__ */ jsx("b", { children: d.applicationsSubmitted })] }),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "Personal statement" }), /* @__PURE__ */ jsx("b", { children: d.essayProgress === 2 ? "Final" : d.essayProgress === 1 ? "Drafted" : "Not started" })] })
								]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "app-progress",
								children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "Test prep steps done" }), /* @__PURE__ */ jsx("b", { children: d.totalTestPrepCompleted })] }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "College steps done" }), /* @__PURE__ */ jsx("b", { children: d.totalCollegePlanningCompleted })] })]
							})
						]
					})]
				})
			]
		})
	});
}
var metricLabels = {
	sat_total: "SAT total",
	sat_math: "SAT math",
	sat_ebrw: "SAT reading & writing",
	act_composite: "ACT composite",
	act_math: "ACT math",
	act_reading: "ACT reading",
	act_science: "ACT science",
	gpa: "GPA",
	colleges_researched: "Colleges researched",
	applications_submitted: "Applications submitted",
	essay_progress: "Essay progress"
};
function TrackerPage() {
	const d = boot.data;
	const metricKeys = Object.keys(d.statHistory || {}).filter((key) => d.statHistory[key]?.length);
	const preferred = d.statHistory?.sat_total?.length ? "sat_total" : d.statHistory?.gpa?.length ? "gpa" : metricKeys[0];
	const [metric, setMetric] = useState(preferred);
	const [historyTab, setHistoryTab] = useState("test");
	const [analysis, setAnalysis] = useState("");
	const [loading, setLoading] = useState(false);
	const analyze = async () => {
		setLoading(true);
		try {
			setAnalysis((await api("/api/tracker-analysis")).analysis);
		} catch (e) {
			setAnalysis(e.message);
		} finally {
			setLoading(false);
		}
	};
	const records = d.statHistory?.[metric] || [];
	const history = historyTab === "test" ? d.testPrepHistory : d.collegePlanningHistory;
	const kpi = d.kpis?.[metric];
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main",
			children: [
				/* @__PURE__ */ jsx(PageIntro, {
					kicker: "PROGRESS TRACKER",
					title: "See the shape of your effort.",
					copy: "Every score you have logged, and every path you have worked through.",
					actions: /* @__PURE__ */ jsxs("button", {
						className: "button button--primary",
						onClick: analyze,
						disabled: loading,
						children: [
							/* @__PURE__ */ jsx(Brain, {}),
							" ",
							loading ? "Analyzing…" : "Analyze my progress"
						]
					})
				}),
				analysis && /* @__PURE__ */ jsxs("article", {
					className: "analysis-panel",
					children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(Sparkles, {}), /* @__PURE__ */ jsx("small", { children: "MENTICS ANALYSIS" })] }), /* @__PURE__ */ jsx(Markdown, { children: analysis })]
				}),
				/* @__PURE__ */ jsx("section", {
					className: "tracker-panel",
					children: metricKeys.length > 0 ? /* @__PURE__ */ jsxs(Fragment, { children: [
						/* @__PURE__ */ jsx("div", {
							className: "metric-switch",
							role: "tablist",
							"aria-label": "Choose a metric",
							children: metricKeys.map((key) => /* @__PURE__ */ jsx("button", {
								role: "tab",
								"aria-selected": metric === key,
								className: metric === key ? "active" : "",
								onClick: () => setMetric(key),
								children: metricLabels[key] || key.replace(/_/g, " ")
							}, key))
						}),
						kpi && /* @__PURE__ */ jsxs("div", {
							className: "kpi-row",
							children: [
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "LATEST" }), /* @__PURE__ */ jsx("b", { children: kpi.latest })] }),
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "BEST" }), /* @__PURE__ */ jsx("b", { children: kpi.best })] }),
								/* @__PURE__ */ jsxs("span", {
									className: kpi.improvement > 0 ? "up" : kpi.improvement < 0 ? "down" : "",
									children: [/* @__PURE__ */ jsx("small", { children: "CHANGE" }), /* @__PURE__ */ jsxs("b", { children: [kpi.improvement > 0 ? "+" : "", Math.round(kpi.improvement * 100) / 100] })]
								})
							]
						}),
						/* @__PURE__ */ jsx(TrendChart, {
							records,
							label: metricLabels[metric] || metric
						}),
						/* @__PURE__ */ jsxs("details", {
							className: "chart-table",
							children: [/* @__PURE__ */ jsx("summary", { children: "View as a table" }), /* @__PURE__ */ jsxs("table", { children: [/* @__PURE__ */ jsx("thead", { children: /* @__PURE__ */ jsxs("tr", { children: [/* @__PURE__ */ jsx("th", { children: "Date" }), /* @__PURE__ */ jsx("th", { children: metricLabels[metric] || metric })] }) }), /* @__PURE__ */ jsx("tbody", { children: records.slice().reverse().map((r, i) => /* @__PURE__ */ jsxs("tr", { children: [/* @__PURE__ */ jsx("td", { children: r.date }), /* @__PURE__ */ jsx("td", { children: r.value })] }, `${r.date}-${i}`)) })] })]
						})
					] }) : /* @__PURE__ */ jsxs("div", {
						className: "chart-empty",
						children: [/* @__PURE__ */ jsx(BarChart3, {}), /* @__PURE__ */ jsx("p", { children: "No scores logged yet. Finish a boss battle or update your scores and your trend line starts here." })]
					})
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "tracker-panel",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "metric-switch",
						role: "tablist",
						"aria-label": "Choose a path",
						children: [/* @__PURE__ */ jsx("button", {
							role: "tab",
							"aria-selected": historyTab === "test",
							className: historyTab === "test" ? "active" : "",
							onClick: () => setHistoryTab("test"),
							children: "Test prep"
						}), /* @__PURE__ */ jsx("button", {
							role: "tab",
							"aria-selected": historyTab === "college",
							className: historyTab === "college" ? "active" : "",
							onClick: () => setHistoryTab("college"),
							children: "College planning"
						})]
					}), history?.length ? /* @__PURE__ */ jsx("ol", {
						className: "unit-history",
						children: history.slice(0, 8).map((gen, i) => {
							const done = gen.tasks.filter((t) => t.is_completed).length;
							return /* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsxs("header", { children: [
								/* @__PURE__ */ jsx("b", { children: gen.tasks[0]?.unit_title || "Unit" }),
								/* @__PURE__ */ jsxs("span", { children: [
									done,
									"/",
									gen.tasks.length,
									" complete"
								] }),
								/* @__PURE__ */ jsx("em", { children: String(gen.date).slice(0, 10) })
							] }), /* @__PURE__ */ jsx("ul", { children: gen.tasks.map((t) => /* @__PURE__ */ jsxs("li", {
								className: t.is_completed ? "done" : "",
								children: [/* @__PURE__ */ jsx("i", { children: t.is_completed ? /* @__PURE__ */ jsx(Check, {}) : t.task_order }), /* @__PURE__ */ jsx("span", { children: t.skill_label || String(t.description).replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").slice(0, 70) })]
							}, t.id)) })] }, `${gen.date}-${i}`);
						})
					}) : /* @__PURE__ */ jsxs("div", {
						className: "chart-empty",
						children: [/* @__PURE__ */ jsx(Target, {}), /* @__PURE__ */ jsxs("p", { children: [
							"No ",
							historyTab === "test" ? "test prep" : "college planning",
							" units yet."
						] })]
					})]
				})
			]
		})
	});
}
var scoreFields = [
	[
		"gpa",
		"GPA",
		"0",
		"5",
		"0.01"
	],
	[
		"sat_ebrw",
		"SAT reading & writing",
		"200",
		"800",
		"10"
	],
	[
		"sat_math",
		"SAT math",
		"200",
		"800",
		"10"
	],
	[
		"act_math",
		"ACT math",
		"1",
		"36",
		"1"
	],
	[
		"act_reading",
		"ACT reading",
		"1",
		"36",
		"1"
	],
	[
		"act_science",
		"ACT science",
		"1",
		"36",
		"1"
	]
];
function EditStats() {
	const d = boot.data;
	const values = {
		gpa: d.gpa,
		sat_ebrw: d.satEbrw,
		sat_math: d.satMath,
		act_math: d.actMath,
		act_reading: d.actReading,
		act_science: d.actScience
	};
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main form-page",
			children: [/* @__PURE__ */ jsx(PageIntro, {
				kicker: "UPDATE PROGRESS",
				title: "Keep your snapshot honest.",
				copy: "New numbers help every future path respond to your real progress."
			}), /* @__PURE__ */ jsxs("form", {
				method: "POST",
				className: "settings-form",
				children: [/* @__PURE__ */ jsx("div", {
					className: "form-field-grid",
					children: scoreFields.map(([name, label, min, max, step]) => /* @__PURE__ */ jsxs("label", { children: [
						label,
						/* @__PURE__ */ jsxs("small", { children: [
							min,
							"–",
							max
						] }),
						/* @__PURE__ */ jsx("input", {
							type: "number",
							name,
							min,
							max,
							step,
							defaultValue: values[name] || ""
						})
					] }, name))
				}), /* @__PURE__ */ jsxs("div", {
					className: "form-actions",
					children: [/* @__PURE__ */ jsx("a", {
						className: "button button--quiet",
						href: "/dashboard/stats",
						children: "Cancel"
					}), /* @__PURE__ */ jsxs("button", {
						className: "button button--primary",
						type: "submit",
						children: ["Save progress ", /* @__PURE__ */ jsx(Check, {})]
					})]
				})]
			})]
		})
	});
}
function Field({ name, label, textarea = false, value, ...props }) {
	return /* @__PURE__ */ jsxs("label", { children: [label, textarea ? /* @__PURE__ */ jsx("textarea", {
		name,
		rows: "4",
		defaultValue: value || "",
		...props
	}) : /* @__PURE__ */ jsx("input", {
		name,
		defaultValue: value || "",
		...props
	})] });
}
var collegeDirectory = [
	"American University",
	"Arizona State University",
	"Auburn University",
	"Barnard College",
	"Baylor University",
	"Boston College",
	"Boston University",
	"Brandeis University",
	"Brown University",
	"Caltech",
	"Carnegie Mellon University",
	"Case Western Reserve University",
	"Clemson University",
	"Colby College",
	"Colgate University",
	"Columbia University",
	"Cornell University",
	"Dartmouth College",
	"Duke University",
	"Emory University",
	"Florida State University",
	"Fordham University",
	"George Washington University",
	"Georgetown University",
	"Georgia Institute of Technology",
	"Harvard University",
	"Howard University",
	"Indiana University Bloomington",
	"Johns Hopkins University",
	"Lehigh University",
	"Louisiana State University",
	"Massachusetts Institute of Technology",
	"Michigan State University",
	"New York University",
	"Northeastern University",
	"North Carolina State University",
	"Northwestern University",
	"Ohio State University",
	"Penn State University",
	"Pomona College",
	"Princeton University",
	"Purdue University",
	"Rice University",
	"Rutgers University",
	"Santa Clara University",
	"Southern Methodist University",
	"Stanford University",
	"Syracuse University",
	"Temple University",
	"Texas A&M University",
	"The University of Texas at Austin",
	"Tufts University",
	"Tulane University",
	"University of Alabama",
	"University of California, Berkeley",
	"University of California, Los Angeles",
	"University of California, San Diego",
	"University of Chicago",
	"University of Colorado Boulder",
	"University of Florida",
	"University of Georgia",
	"University of Illinois Urbana-Champaign",
	"University of Maryland, College Park",
	"University of Miami",
	"University of Michigan",
	"University of North Carolina at Chapel Hill",
	"University of Notre Dame",
	"University of Pennsylvania",
	"University of Richmond",
	"University of Southern California",
	"University of Virginia",
	"University of Washington",
	"University of Wisconsin–Madison",
	"Vanderbilt University",
	"Virginia Tech",
	"Wake Forest University",
	"Washington University in St. Louis",
	"Wellesley College",
	"Williams College",
	"Yale University"
];
function CollegePicker({ value = "" }) {
	const [query, setQuery] = useState("");
	const [selected, setSelected] = useState(() => String(value).split(",").map((item) => item.trim()).filter(Boolean));
	const normalized = query.trim().toLowerCase();
	const matches = normalized ? collegeDirectory.filter((name) => name.toLowerCase().includes(normalized) && !selected.includes(name)).slice(0, 6) : [];
	const addCollege = (name) => {
		setSelected((items) => items.includes(name) ? items : [...items, name]);
		setQuery("");
	};
	return /* @__PURE__ */ jsxs("fieldset", {
		className: "college-picker",
		children: [
			/* @__PURE__ */ jsxs("legend", { children: ["Start your college list ", /* @__PURE__ */ jsx("span", { children: "optional" })] }),
			/* @__PURE__ */ jsx("p", { children: "Search a school, then add it to the plan Mentics uses to personalize your assignments." }),
			/* @__PURE__ */ jsx("input", {
				type: "hidden",
				name: "target_colleges",
				value: selected.join(", ")
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "college-search",
				children: [/* @__PURE__ */ jsx(Search, { "aria-hidden": "true" }), /* @__PURE__ */ jsx("input", {
					value: query,
					onChange: (event) => setQuery(event.target.value),
					placeholder: "Search colleges",
					"aria-label": "Search colleges",
					autoComplete: "off"
				})]
			}),
			matches.length > 0 && /* @__PURE__ */ jsx("div", {
				className: "college-results",
				role: "listbox",
				"aria-label": "College suggestions",
				children: matches.map((name) => /* @__PURE__ */ jsxs("button", {
					type: "button",
					role: "option",
					onClick: () => addCollege(name),
					children: [/* @__PURE__ */ jsx("span", { children: name }), /* @__PURE__ */ jsx(Plus, { "aria-hidden": "true" })]
				}, name))
			}),
			selected.length > 0 ? /* @__PURE__ */ jsx("div", {
				className: "college-chips",
				"aria-label": "Selected colleges",
				children: selected.map((name) => /* @__PURE__ */ jsxs("span", { children: [name, /* @__PURE__ */ jsx("button", {
					type: "button",
					onClick: () => setSelected((items) => items.filter((item) => item !== name)),
					"aria-label": `Remove ${name}`,
					children: /* @__PURE__ */ jsx(X, {})
				})] }, name))
			}) : /* @__PURE__ */ jsxs("div", {
				className: "college-picker-empty",
				children: [/* @__PURE__ */ jsx(GraduationCap, {}), /* @__PURE__ */ jsx("span", { children: "No schools selected yet — you can build a strong plan before your list is final." })]
			})
		]
	});
}
function BuilderPage({ kind }) {
	const d = boot.data;
	const test = kind === "test";
	const [focus, setFocus] = useState(d.test_focus || "");
	const [stage, setStage] = useState(d.planning_stage || "");
	const showsSat = focus === "sat" || focus === "both";
	const showsAct = focus === "act" || focus === "both";
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main form-page",
			children: [/* @__PURE__ */ jsx(PageIntro, {
				kicker: test ? "TEST PREPARATION" : "COLLEGE PLANNING",
				title: test ? "Build a plan for the test you are taking." : "Build a college plan with a point of view.",
				copy: test ? "Choose SAT, ACT, or both. Mentics will only ask for the scores that matter to that choice." : "Your grade, current stage, priorities, and school list become the context behind every lesson and assignment."
			}), /* @__PURE__ */ jsxs("form", {
				method: "POST",
				className: "settings-form builder-form",
				children: [test ? /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsxs("fieldset", { children: [
					/* @__PURE__ */ jsx("legend", { children: "What are you preparing for?" }),
					/* @__PURE__ */ jsx("p", {
						className: "builder-help",
						children: "Switching focus immediately reshapes the score fields below."
					}),
					/* @__PURE__ */ jsx("div", {
						className: "choice-grid choice-grid--three",
						children: [
							[
								"sat",
								"SAT only",
								"One focused score plan"
							],
							[
								"act",
								"ACT only",
								"One focused score plan"
							],
							[
								"both",
								"SAT + ACT",
								"Compare before committing"
							]
						].map(([value, label, copy]) => /* @__PURE__ */ jsxs("label", {
							className: focus === value ? "selected" : "",
							children: [
								/* @__PURE__ */ jsx("input", {
									type: "radio",
									name: "test_focus",
									value,
									required: true,
									checked: focus === value,
									onChange: () => setFocus(value)
								}),
								/* @__PURE__ */ jsx(BookOpen, {}),
								/* @__PURE__ */ jsx("b", { children: label }),
								/* @__PURE__ */ jsx("small", { children: copy })
							]
						}, value))
					})
				] }), focus && /* @__PURE__ */ jsxs("div", {
					className: "builder-score-groups",
					children: [
						showsSat && /* @__PURE__ */ jsxs("fieldset", {
							className: "builder-score-group",
							children: [
								/* @__PURE__ */ jsx("legend", { children: "SAT goals and baseline" }),
								/* @__PURE__ */ jsx("p", { children: "Use your latest official or full-length practice scores if you have them." }),
								/* @__PURE__ */ jsxs("div", {
									className: "form-field-grid",
									children: [
										/* @__PURE__ */ jsx(Field, {
											name: "desired_sat",
											label: "Goal SAT score",
											type: "number",
											min: "400",
											max: "1600",
											step: "10",
											value: d.desired_sat
										}),
										/* @__PURE__ */ jsx(Field, {
											name: "current_sat_ebrw",
											label: "Current Reading & Writing",
											type: "number",
											min: "200",
											max: "800",
											value: d.current_sat_ebrw
										}),
										/* @__PURE__ */ jsx(Field, {
											name: "current_sat_math",
											label: "Current Math",
											type: "number",
											min: "200",
											max: "800",
											value: d.current_sat_math
										})
									]
								})
							]
						}),
						showsAct && /* @__PURE__ */ jsxs("fieldset", {
							className: "builder-score-group",
							children: [
								/* @__PURE__ */ jsx("legend", { children: "ACT goals and baseline" }),
								/* @__PURE__ */ jsx("p", { children: "Use your latest composite and section scores if you have them." }),
								/* @__PURE__ */ jsxs("div", {
									className: "form-field-grid",
									children: [
										/* @__PURE__ */ jsx(Field, {
											name: "desired_act",
											label: "Goal ACT score",
											type: "number",
											min: "1",
											max: "36",
											value: d.desired_act
										}),
										/* @__PURE__ */ jsx(Field, {
											name: "current_act_composite",
											label: "Current composite",
											type: "number",
											min: "1",
											max: "36",
											value: d.current_act_composite
										}),
										/* @__PURE__ */ jsx(Field, {
											name: "current_act_math",
											label: "Current Math",
											type: "number",
											min: "1",
											max: "36",
											value: d.current_act_math
										}),
										/* @__PURE__ */ jsx(Field, {
											name: "current_act_reading",
											label: "Current Reading",
											type: "number",
											min: "1",
											max: "36",
											value: d.current_act_reading
										}),
										/* @__PURE__ */ jsx(Field, {
											name: "current_act_science",
											label: "Current Science",
											type: "number",
											min: "1",
											max: "36",
											value: d.current_act_science
										})
									]
								})
							]
						}),
						/* @__PURE__ */ jsxs("fieldset", {
							className: "builder-score-group builder-score-group--shared",
							children: [
								/* @__PURE__ */ jsx("legend", { children: "Your study reality" }),
								/* @__PURE__ */ jsxs("div", {
									className: "form-field-grid",
									children: [/* @__PURE__ */ jsx(Field, {
										name: "hours_per_week",
										label: "Hours available each week",
										type: "number",
										min: "1",
										max: "40",
										value: d.hours_per_week
									}), /* @__PURE__ */ jsx(Field, {
										name: "test_date",
										label: "Test date",
										type: "date",
										value: d.test_date
									})]
								}),
								/* @__PURE__ */ jsx(Field, {
									name: "strengths",
									label: "Your strengths",
									textarea: true,
									value: d.strengths
								}),
								/* @__PURE__ */ jsx(Field, {
									name: "weaknesses",
									label: "Where you need the most help",
									textarea: true,
									required: true,
									value: d.weaknesses
								})
							]
						})
					]
				})] }) : /* @__PURE__ */ jsxs(Fragment, { children: [
					/* @__PURE__ */ jsxs("div", {
						className: "college-plan-steps",
						"aria-label": "College plan setup",
						children: [
							/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "01" }), " Your starting point"] }),
							/* @__PURE__ */ jsx("i", {}),
							/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "02" }), " Your direction"] }),
							/* @__PURE__ */ jsx("i", {}),
							/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "03" }), " Your list"] })
						]
					}),
					/* @__PURE__ */ jsxs("fieldset", {
						className: "builder-score-group",
						children: [/* @__PURE__ */ jsx("legend", { children: "Where are you right now?" }), /* @__PURE__ */ jsx("div", {
							className: "form-field-grid",
							children: /* @__PURE__ */ jsxs("label", { children: ["Current grade", /* @__PURE__ */ jsxs("select", {
								name: "current_grade",
								required: true,
								defaultValue: d.grade || "",
								children: [/* @__PURE__ */ jsx("option", {
									value: "",
									children: "Choose grade"
								}), [
									"9",
									"10",
									"11",
									"12"
								].map((v) => /* @__PURE__ */ jsxs("option", {
									value: v,
									children: [v, "th grade"]
								}, v))]
							})] })
						})]
					}),
					/* @__PURE__ */ jsxs("fieldset", { children: [/* @__PURE__ */ jsx("legend", { children: "What should this plan move forward?" }), /* @__PURE__ */ jsx("div", {
						className: "choice-grid choice-grid--three",
						children: [
							[
								"exploring",
								"Explore",
								"Clarify what matters before building a list"
							],
							[
								"researching",
								"Research",
								"Turn possible schools into informed choices"
							],
							[
								"applying",
								"Apply",
								"Move essays and applications forward"
							]
						].map(([value, label, copy]) => /* @__PURE__ */ jsxs("label", {
							className: stage === value ? "selected" : "",
							children: [
								/* @__PURE__ */ jsx("input", {
									type: "radio",
									name: "planning_stage",
									value,
									required: true,
									checked: stage === value,
									onChange: () => setStage(value)
								}),
								/* @__PURE__ */ jsx(Target, {}),
								/* @__PURE__ */ jsx("b", { children: label }),
								/* @__PURE__ */ jsx("small", { children: copy })
							]
						}, value))
					})] }),
					/* @__PURE__ */ jsxs("fieldset", {
						className: "builder-score-group",
						children: [
							/* @__PURE__ */ jsx("legend", { children: "What matters to you?" }),
							/* @__PURE__ */ jsx("p", { children: "Tell Mentics what should lead your decisions, not just what looks impressive." }),
							/* @__PURE__ */ jsx(Field, {
								name: "interested_majors",
								label: "Possible majors or interests",
								textarea: true,
								value: d.majors
							}),
							/* @__PURE__ */ jsx(Field, {
								name: "college_priorities",
								label: "Your college priorities",
								textarea: true,
								value: d.priorities,
								placeholder: "Examples: engineering opportunities, an active campus, affordability, being close to home, strong arts programs"
							})
						]
					}),
					/* @__PURE__ */ jsx(CollegePicker, { value: d.target_colleges })
				] }), /* @__PURE__ */ jsxs("div", {
					className: "form-actions",
					children: [/* @__PURE__ */ jsx("a", {
						className: "button button--quiet",
						href: "/dashboard",
						children: "Cancel"
					}), /* @__PURE__ */ jsxs("button", {
						className: "button button--primary",
						type: "submit",
						children: ["Build my path ", /* @__PURE__ */ jsx(ArrowRight, {})]
					})]
				})]
			})]
		})
	});
}
function ForumPage() {
	const d = boot.data;
	const [creating, setCreating] = useState(false);
	const [busy, setBusy] = useState(false);
	const [editing, setEditing] = useState(null);
	const [error, setError] = useState("");
	const submitPost = async (e) => {
		e.preventDefault();
		setBusy(true);
		setError("");
		const form = new FormData(e.currentTarget);
		try {
			await api("/api/posts", {
				method: "POST",
				body: JSON.stringify({
					title: form.get("title"),
					content: form.get("content")
				})
			});
			window.location.reload();
		} catch (x) {
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	const reply = async (postId, e) => {
		e.preventDefault();
		setBusy(true);
		setError("");
		const form = new FormData(e.currentTarget);
		try {
			await api("/api/replies", {
				method: "POST",
				body: JSON.stringify({
					post_id: postId,
					content: form.get("content")
				})
			});
			window.location.reload();
		} catch (x) {
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	const saveEdit = async (kind, id, e) => {
		e.preventDefault();
		setBusy(true);
		setError("");
		const form = new FormData(e.currentTarget);
		const payload = kind === "post" ? {
			title: form.get("title"),
			content: form.get("content")
		} : { content: form.get("content") };
		try {
			await api(`/api/${kind === "post" ? "posts" : "replies"}/${id}`, {
				method: "PATCH",
				body: JSON.stringify(payload)
			});
			window.location.reload();
		} catch (x) {
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	const editingItem = (kind, id) => editing?.kind === kind && editing?.id === id;
	const editButton = (kind, item) => /* @__PURE__ */ jsxs("button", {
		type: "button",
		className: "forum-edit",
		onClick: () => setEditing({
			kind,
			id: item.id
		}),
		children: [/* @__PURE__ */ jsx(PenLine, { size: 14 }), " Edit"]
	});
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main",
			children: [
				/* @__PURE__ */ jsx(PageIntro, {
					kicker: "MENTICS COMMUNITY",
					title: "Students helping students.",
					copy: "Compare approaches, ask better questions, and move forward together.",
					actions: /* @__PURE__ */ jsxs("button", {
						className: "button button--primary",
						onClick: () => setCreating(!creating),
						children: [/* @__PURE__ */ jsx(Plus, {}), " New discussion"]
					})
				}),
				error && /* @__PURE__ */ jsx("p", {
					className: "form-error",
					children: error
				}),
				creating && /* @__PURE__ */ jsxs("form", {
					className: "new-post-panel",
					onSubmit: submitPost,
					children: [
						/* @__PURE__ */ jsx(Field, {
							name: "title",
							label: "Discussion title",
							required: true
						}),
						/* @__PURE__ */ jsx(Field, {
							name: "content",
							label: "What do you want to share or ask?",
							textarea: true,
							required: true
						}),
						/* @__PURE__ */ jsx("button", {
							className: "button button--primary",
							disabled: busy,
							children: "Publish discussion"
						})
					]
				}),
				/* @__PURE__ */ jsxs("form", {
					className: "forum-search",
					method: "GET",
					children: [
						/* @__PURE__ */ jsx(Search, {}),
						/* @__PURE__ */ jsx("input", {
							name: "search",
							defaultValue: d.searchQuery || "",
							placeholder: "Search discussions"
						}),
						/* @__PURE__ */ jsx("button", { children: "Search" })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "forum-layout",
					children: [/* @__PURE__ */ jsx("div", {
						className: "thread-list",
						children: d.posts?.length ? d.posts.map((post) => /* @__PURE__ */ jsxs("article", {
							className: "thread",
							children: [
								/* @__PURE__ */ jsxs("header", { children: [
									/* @__PURE__ */ jsx("span", { children: String(post.user_name || "M").slice(0, 1) }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: post.title }), /* @__PURE__ */ jsxs("small", { children: [
										post.user_name,
										" · ",
										String(post.created_at).slice(0, 10)
									] })] }),
									post.user_id === d.viewerId && !editingItem("post", post.id) && editButton("post", post)
								] }),
								editingItem("post", post.id) ? /* @__PURE__ */ jsxs("form", {
									className: "forum-edit-form",
									onSubmit: (e) => saveEdit("post", post.id, e),
									children: [
										/* @__PURE__ */ jsx("input", {
											name: "title",
											defaultValue: post.title,
											maxLength: "200",
											required: true
										}),
										/* @__PURE__ */ jsx("textarea", {
											name: "content",
											defaultValue: post.content,
											maxLength: "5000",
											required: true
										}),
										/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("button", {
											className: "button button--primary",
											disabled: busy,
											children: "Save changes"
										}), /* @__PURE__ */ jsx("button", {
											type: "button",
											className: "button button--quiet",
											onClick: () => setEditing(null),
											children: "Cancel"
										})] })
									]
								}) : /* @__PURE__ */ jsx("p", { children: post.content }),
								post.replies?.length > 0 && /* @__PURE__ */ jsx("div", {
									className: "replies",
									children: post.replies.map((r) => /* @__PURE__ */ jsx("div", { children: editingItem("reply", r.id) ? /* @__PURE__ */ jsxs("form", {
										className: "forum-edit-form",
										onSubmit: (e) => saveEdit("reply", r.id, e),
										children: [/* @__PURE__ */ jsx("textarea", {
											name: "content",
											defaultValue: r.content,
											maxLength: "5000",
											required: true
										}), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("button", {
											className: "button button--primary",
											disabled: busy,
											children: "Save"
										}), /* @__PURE__ */ jsx("button", {
											type: "button",
											className: "button button--quiet",
											onClick: () => setEditing(null),
											children: "Cancel"
										})] })]
									}) : /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsxs("div", {
										className: "reply-meta",
										children: [/* @__PURE__ */ jsx("b", { children: r.user_name }), r.user_id === d.viewerId && editButton("reply", r)]
									}), /* @__PURE__ */ jsx("p", { children: r.content })] }) }, r.id))
								}),
								/* @__PURE__ */ jsxs("form", {
									onSubmit: (e) => reply(post.id, e),
									children: [/* @__PURE__ */ jsx("input", {
										name: "content",
										required: true,
										placeholder: "Add a thoughtful reply"
									}), /* @__PURE__ */ jsx("button", {
										disabled: busy,
										children: /* @__PURE__ */ jsx(Send, {})
									})]
								})
							]
						}, post.id)) : /* @__PURE__ */ jsxs("div", {
							className: "empty-state",
							children: [/* @__PURE__ */ jsx(MessageCircle, {}), /* @__PURE__ */ jsx("p", { children: "No discussions match this search yet." })]
						})
					}), /* @__PURE__ */ jsxs("aside", {
						className: "community-aside",
						children: [
							/* @__PURE__ */ jsx(UsersRound, {}),
							/* @__PURE__ */ jsx("h3", { children: "Today in Mentics" }),
							/* @__PURE__ */ jsx("strong", { children: d.todaysThreads?.length || 0 }),
							/* @__PURE__ */ jsx("span", { children: "new discussions" }),
							/* @__PURE__ */ jsx("p", { children: "Keep posts specific, respectful, and useful to the next student." })
						]
					})]
				})
			]
		})
	});
}
function PointsPage() {
	const d = boot.data;
	const achievements = d.achievements || [];
	const earned = achievements.filter((item) => item.is_earned).length;
	const iconFor = (id) => id.startsWith("points_") ? Zap : id.startsWith("streak_") ? Flame : id === "first_step" ? Check : Trophy;
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main points-page",
			children: [
				/* @__PURE__ */ jsx(PageIntro, {
					kicker: "YOUR MOMENTUM",
					title: "Track progress that belongs to you.",
					copy: "Your points, streak, and achievements are private—built to help you notice your own consistency."
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "points-overview",
					"aria-label": "Your points summary",
					children: [
						/* @__PURE__ */ jsxs("article", {
							className: "points-total",
							children: [
								/* @__PURE__ */ jsx("small", { children: "TOTAL POINTS" }),
								/* @__PURE__ */ jsx("strong", { children: Number(d.points || 0).toLocaleString() }),
								/* @__PURE__ */ jsx("p", { children: "Earned from completed work" })
							]
						}),
						/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx(Flame, {}), /* @__PURE__ */ jsxs("div", { children: [
							/* @__PURE__ */ jsx("small", { children: "DAY STREAK" }),
							/* @__PURE__ */ jsx("strong", { children: d.streak || 0 }),
							/* @__PURE__ */ jsx("p", { children: "Keep showing up one day at a time" })
						] })] }),
						/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx(Award, {}), /* @__PURE__ */ jsxs("div", { children: [
							/* @__PURE__ */ jsx("small", { children: "ACHIEVEMENTS" }),
							/* @__PURE__ */ jsxs("strong", { children: [earned, /* @__PURE__ */ jsxs("span", { children: ["/", achievements.length] })] }),
							/* @__PURE__ */ jsx("p", { children: "Unlocked on your path" })
						] })] })
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "achievements-panel",
					children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: "YOUR COLLECTION" }), /* @__PURE__ */ jsx("h2", { children: "Achievements" })] }), /* @__PURE__ */ jsxs("span", { children: [earned, " unlocked"] })] }), /* @__PURE__ */ jsx("div", {
						className: "achievements-grid",
						children: achievements.map((item) => {
							const Icon = iconFor(item.id);
							return /* @__PURE__ */ jsxs("article", {
								className: item.is_earned ? "is-earned" : "is-locked",
								children: [
									/* @__PURE__ */ jsx("i", { children: item.is_earned ? /* @__PURE__ */ jsx(Icon, {}) : /* @__PURE__ */ jsx(LockKeyhole, {}) }),
									/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("b", { children: item.title }), /* @__PURE__ */ jsx("p", { children: item.description })] }),
									/* @__PURE__ */ jsx("span", { children: item.is_earned ? /* @__PURE__ */ jsx(Check, {}) : "Locked" })
								]
							}, item.id);
						})
					})]
				})
			]
		})
	});
}
function AccountPage() {
	const d = boot.data;
	const confirmDeletion = (event) => {
		if (!window.confirm("Delete your Mentics account and all associated data? This cannot be undone.")) event.preventDefault();
	};
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main form-page",
			children: [
				/* @__PURE__ */ jsx(PageIntro, {
					kicker: "YOUR ACCOUNT",
					title: "Make Mentics yours.",
					copy: "Keep your identity and sign-in details current."
				}),
				d.updated && /* @__PURE__ */ jsxs("div", {
					className: "success-banner",
					children: [/* @__PURE__ */ jsx(Check, {}), " Your account was updated."]
				}),
				d.error && /* @__PURE__ */ jsx("div", {
					className: "form-error",
					children: d.error
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "account-sections",
					children: [
						/* @__PURE__ */ jsxs("form", {
							method: "POST",
							children: [
								/* @__PURE__ */ jsx(CsrfField, {}),
								/* @__PURE__ */ jsx("input", {
									type: "hidden",
									name: "form_type",
									value: "name"
								}),
								/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(UserRound, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("h2", { children: "Your name" }), /* @__PURE__ */ jsx("p", { children: "How Mentics addresses you." })] })] }),
								/* @__PURE__ */ jsx(Field, {
									name: "name",
									label: "Full name",
									value: d.name,
									required: true,
									maxLength: "100"
								}),
								/* @__PURE__ */ jsx("button", {
									className: "button button--primary",
									children: "Save name"
								})
							]
						}),
						/* @__PURE__ */ jsxs("form", {
							method: "POST",
							children: [
								/* @__PURE__ */ jsx(CsrfField, {}),
								/* @__PURE__ */ jsx("input", {
									type: "hidden",
									name: "form_type",
									value: "email"
								}),
								/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(Mail, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("h2", { children: "Email address" }), /* @__PURE__ */ jsx("p", { children: "Where you sign in." })] })] }),
								/* @__PURE__ */ jsx(Field, {
									name: "email",
									label: "Email",
									type: "email",
									value: d.email,
									required: true,
									maxLength: "254"
								}),
								/* @__PURE__ */ jsx("button", {
									className: "button button--primary",
									children: "Save email"
								})
							]
						}),
						/* @__PURE__ */ jsxs("form", {
							method: "POST",
							children: [
								/* @__PURE__ */ jsx(CsrfField, {}),
								/* @__PURE__ */ jsx("input", {
									type: "hidden",
									name: "form_type",
									value: "password"
								}),
								/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(ShieldCheck, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("h2", { children: "Password" }), /* @__PURE__ */ jsx("p", { children: "Use at least eight characters." })] })] }),
								/* @__PURE__ */ jsx(Field, {
									name: "current_password",
									label: "Current password",
									type: "password",
									required: true,
									maxLength: "128"
								}),
								/* @__PURE__ */ jsx(Field, {
									name: "new_password",
									label: "New password",
									type: "password",
									minLength: "8",
									maxLength: "128",
									required: true
								}),
								/* @__PURE__ */ jsx(Field, {
									name: "confirm_password",
									label: "Confirm new password",
									type: "password",
									minLength: "8",
									maxLength: "128",
									required: true
								}),
								/* @__PURE__ */ jsx("button", {
									className: "button button--primary",
									children: "Change password"
								})
							]
						})
					]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "account-danger-zone",
					children: [
						/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsx(AlertTriangle, {}), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("small", { children: "DATA & ACCOUNT" }), /* @__PURE__ */ jsx("h2", { children: "Delete your account" })] })] }),
						/* @__PURE__ */ jsx("p", { children: "This permanently deletes your profile, paths, scores, answers, AI chat history, Arena record, and content you posted. Discussion threads you started are removed with their replies." }),
						/* @__PURE__ */ jsxs("form", {
							method: "POST",
							onSubmit: confirmDeletion,
							children: [
								/* @__PURE__ */ jsx(CsrfField, {}),
								/* @__PURE__ */ jsx("input", {
									type: "hidden",
									name: "form_type",
									value: "delete_account"
								}),
								/* @__PURE__ */ jsx(Field, {
									name: "delete_email",
									label: "Type your account email",
									type: "email",
									required: true,
									autoComplete: "off",
									maxLength: "254"
								}),
								/* @__PURE__ */ jsx(Field, {
									name: "delete_confirmation",
									label: "Type DELETE to confirm",
									required: true,
									autoComplete: "off",
									pattern: "DELETE"
								}),
								/* @__PURE__ */ jsx("button", {
									className: "button account-delete-button",
									type: "submit",
									children: "Delete account and data"
								})
							]
						})
					]
				}),
				/* @__PURE__ */ jsxs("form", {
					className: "logout-link",
					method: "POST",
					action: "/logout",
					children: [/* @__PURE__ */ jsx(CsrfField, {}), /* @__PURE__ */ jsxs("button", {
						type: "submit",
						children: ["Sign out of Mentics ", /* @__PURE__ */ jsx(ArrowRight, {})]
					})]
				})
			]
		})
	});
}
var legalCopy = {
	privacy: {
		title: "Privacy Policy",
		date: "August 23, 2026",
		intro: "Welcome to Mentics. This policy explains how Mentics collects, uses, discloses, and safeguards information when you use our website and services.",
		sections: [
			["1. Information we collect", "We collect account information such as your name, email, and securely hashed password or Google profile details. Educational data can include goals, learning style, anxieties, GPA, SAT/ACT scores, strengths, weaknesses, test dates, grade level, majors, and target colleges. We also collect content you choose to submit, including forum posts and replies, AI-assistant conversations, essays and prompts, plus activity data such as completed tasks, generated paths, and stat updates. Our servers may also receive technical information such as IP address, browser, operating system, access times, and viewed pages."],
			["2. How we use information", "We use this information to create and manage accounts; generate personalized test-prep and college-planning paths; provide contextual chat and essay feedback; operate the forum; display private progress; analyze and improve Mentics; and administer points, streaks, and achievements."],
			["3. Disclosure of information", "Mentics does not sell personal information. We may disclose information when required by law or needed to protect rights, property, and safety. We share inputs such as chat messages and essay text with Google Gemini only to provide the AI features you request, subject to Google’s privacy policies. We do not currently share user information with third-party advertisers."],
			["4. Children's privacy", "Mentics is intended for high school students generally over age 13. We do not knowingly collect personally identifiable information from children under 13. If we learn that a user is under 13, we will require verifiable parental consent; parents or guardians may contact us to request appropriate action."],
			["5. Your rights and choices", "You may review or change account information from account settings and may contact us to opt out of communications or ask about your information."],
			["6. Security", "We use administrative, technical, and physical safeguards designed to protect personal information. No security measure or method of transmission can be guaranteed against every interception or misuse."],
			["7. Cookies and authentication", "Mentics uses essential cookies and similar technologies to maintain sessions, remember security state, prevent abuse, and operate the service. Google sign-in uses the openid, email, and profile scopes; we do not request access to Gmail, Google Drive, Calendar, or other Google content."],
			["8. AI processing", "When you request AI chat, path generation, assignment feedback, or essay feedback, the relevant input and necessary path context may be sent to an AI service provider to produce that feature. AI outputs may be inaccurate or incomplete and are not professional, admissions, legal, medical, financial, or mental-health advice. Do not submit content you do not want processed for the feature you requested."],
			["9. Public community content", "Forum posts, replies, display name, and other content you choose to make public may be visible to other users and may be copied by them. Do not publish private contact details, account credentials, educational records, or another person’s information without permission."],
			["10. Retention", "We retain information for as long as reasonably necessary to operate Mentics, maintain security, resolve disputes, enforce agreements, and meet legal obligations. Retention varies by purpose. We may retain aggregated or de-identified information that does not reasonably identify you."],
			["11. Your privacy choices and rights", "You may update certain account and academic information in Mentics. Subject to applicable law, you may request access, correction, deletion, or a copy of personal information by emailing us. We may verify requests and may retain limited information where needed for security, fraud prevention, legal compliance, or legitimate operations."],
			["12. California and other regional rights", "Mentics does not sell personal information or share it for cross-context behavioral advertising. California residents and residents of other jurisdictions may have additional rights under applicable law, including rights to know, correct, delete, or limit certain uses. Contact us to make a request."],
			["13. International transfers", "Mentics is operated from the United States. If you access it from elsewhere, your information may be processed in the United States or other places where our service providers operate, which may have different privacy laws."],
			["14. Changes to this policy", "We may update this policy as the service or law changes. We will post the revised version and update the Last updated date; where required, we will provide additional notice or obtain consent."],
			["15. Contact us", "Questions, privacy requests, or complaints can be sent to thementicsapp@gmail.com."]
		]
	},
	terms: {
		title: "Terms of Service",
		date: "August 23, 2026",
		intro: "Please read these terms carefully before using the Mentics website and services. Creating an account, accessing, or using Mentics means you agree to these Terms and our Privacy Policy.",
		sections: [
			["1. Agreement to terms", "If you disagree with any part of these terms, you may not access the service."],
			["2. Description of service", "Mentics provides personalized AI-generated SAT/ACT and college-planning paths, contextual guidance, academic progress tracking, points, streaks and achievements, a community forum, and AI-driven essay analysis."],
			["3. Accounts and eligibility", "You must be at least 13 years old. You are responsible for accurate and complete account information, safeguarding your password, and activity under your credentials."],
			["4. User-generated content", "You are responsible for the legality, reliability, and appropriateness of content you submit. By posting content, you grant Mentics a non-exclusive, worldwide, royalty-free, perpetual, transferable license to use, reproduce, modify, display, and distribute it in connection with providing and improving the service. You represent that you have the required rights. Mentics may monitor or remove content that violates these terms or is harmful or objectionable."],
			["5. AI and API usage", "Mentics uses third-party AI services including Google Gemini and is committed to responsible use. AI-generated paths, chat responses, and essay feedback are educational information only and may be inaccurate. You are responsible for verification and judgment."],
			["6. Prohibited activities", "Do not use Mentics illegally, harass or defraud users, post obscene, defamatory, hateful, infringing, or harmful content, compromise system security, decipher server transmissions, or submit false or misleading information."],
			["7. Copyright policy and DMCA", "We respect intellectual-property rights. Send a detailed claim that meets DMCA requirements to thementicsapp@gmail.com with the subject “Copyright Infringement.”"],
			["8. Disclaimers and trademark notice", "Mentics is independent and is not affiliated with, endorsed by, or sponsored by the College Board®, owner of the SAT®, or ACT®, Inc., owner of the ACT®. AI content and the service are provided “as is” and “as available,” without express or implied warranties."],
			["9. Independence from tests and institutions", "MENTICS IS INDEPENDENT. Mentics is not affiliated with, endorsed by, sponsored by, approved by, or acting on behalf of the College Board, SAT, ACT, ACT, Inc., any school, university, college, admissions office, scholarship provider, or government agency. References to tests, schools, trademarks, or third-party resources are for identification and educational purposes only."],
			["10. Educational and AI disclaimer", "Mentics, including AI-generated paths, lessons, coaching, and essay feedback, provides general educational information only. It does not guarantee scores, admission, scholarships, financial aid, or any outcome. AI may be inaccurate, incomplete, biased, or out of date. Verify deadlines, requirements, score policies, and admissions information directly with the relevant official source before acting."],
			["11. Third-party services", "Mentics may link to or use third-party services, including Google sign-in, AI providers, official test resources, and college websites. Their content, availability, privacy practices, and terms are outside our control and your use is governed by their policies."],
			["12. Termination", "Mentics may terminate or suspend an account immediately and without prior notice or liability, including for a breach of these terms."],
			["13. Governing law and disputes", "These terms are governed by the laws of Georgia, United States. Before filing a claim, contact us and attempt to resolve the issue informally for 30 days. Nothing in these Terms limits non-waivable consumer rights or a claim properly brought in small-claims court."],
			["14. Limitation of liability", "TO THE MAXIMUM EXTENT PERMITTED BY LAW, Mentics and its directors, employees, agents, and providers are not liable for indirect, incidental, special, consequential, exemplary, or punitive damages, including loss of data, goodwill, profits, scores, admissions opportunities, or other intangible losses arising from the service or its content."],
			["15. Changes", "Mentics may modify these Terms by posting an updated version and changing the Last updated date. Continued use after the effective date means you accept the updated Terms, except where applicable law requires a different form of notice or consent."],
			["16. Contact us", "Questions about these terms can be sent to thementicsapp@gmail.com."]
		]
	}
};
function LegalPage({ type }) {
	const d = legalCopy[type];
	return /* @__PURE__ */ jsxs("div", {
		className: "legal-page",
		children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsx(Brand, {}), /* @__PURE__ */ jsxs("a", {
			href: "/",
			children: [/* @__PURE__ */ jsx(ArrowLeft, {}), " Back to Mentics"]
		})] }), /* @__PURE__ */ jsxs("main", { children: [
			/* @__PURE__ */ jsxs("div", {
				className: "legal-title",
				children: [
					/* @__PURE__ */ jsx("small", { children: "MENTICS LEGAL" }),
					/* @__PURE__ */ jsx("h1", { children: d.title }),
					/* @__PURE__ */ jsxs("p", { children: ["Last updated ", d.date] })
				]
			}),
			/* @__PURE__ */ jsx("p", {
				className: "legal-intro",
				children: d.intro
			}),
			d.sections.map(([title, copy]) => /* @__PURE__ */ jsxs("section", { children: [/* @__PURE__ */ jsx("h2", { children: title }), /* @__PURE__ */ jsx("p", { children: copy })] }, title))
		] })]
	});
}
function ArticlePage() {
	const d = boot.data;
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: "app-main article-page",
			children: [/* @__PURE__ */ jsxs("a", {
				href: "/dashboard/test-path-view",
				className: "text-button",
				children: [/* @__PURE__ */ jsx(ArrowLeft, {}), " Back to path"]
			}), /* @__PURE__ */ jsxs("article", { children: [
				/* @__PURE__ */ jsxs("div", {
					className: "eyebrow",
					children: [/* @__PURE__ */ jsx("span", {}), " STRATEGY GUIDE"]
				}),
				/* @__PURE__ */ jsx("h1", { children: d.article?.title }),
				/* @__PURE__ */ jsx(Markdown, { children: d.article?.content || "This article is not available yet." })
			] })]
		})
	});
}
function App() {
	useEffect(() => {
		document.documentElement.dataset.menticsPage = boot.page;
		const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
		const nodes = [...document.querySelectorAll(".app-main > :not(.chat-panel),.onboarding-page main > form > section.active,.auth-panel > *")];
		if (!reduced) {
			nodes.slice(0, 8).forEach((node, index) => {
				node.classList.add("mx-app-enter");
				node.style.setProperty("--mx-enter-delay", `${Math.min(index, 5) * 35}ms`);
			});
			requestAnimationFrame(() => requestAnimationFrame(() => nodes.forEach((node) => node.classList.add("is-present"))));
		}
		return () => {
			delete document.documentElement.dataset.menticsPage;
		};
	}, []);
	let page;
	switch (boot.page) {
		case "dashboard":
			page = /* @__PURE__ */ jsx(Dashboard, {});
			break;
		case "path":
			page = /* @__PURE__ */ jsx(PathPage, {});
			break;
		case "battles":
			page = /* @__PURE__ */ jsx(ArenaRouteBoundary, { children: /* @__PURE__ */ jsx(Suspense, {
				fallback: /* @__PURE__ */ jsx(AppShell, {
					name: boot.data.name,
					children: /* @__PURE__ */ jsxs("main", {
						className: "app-main",
						role: "status",
						children: [/* @__PURE__ */ jsx("h1", { children: "Entering the Arena" }), /* @__PURE__ */ jsx("p", { children: "Preparing your lobby and loadout…" })]
					})
				}),
				children: /* @__PURE__ */ jsx(BattleArena, {})
			}) });
			break;
		case "login":
			page = /* @__PURE__ */ jsx(AuthPage, { mode: "login" });
			break;
		case "signup":
			page = /* @__PURE__ */ jsx(AuthPage, { mode: "signup" });
			break;
		case "onboarding":
			page = /* @__PURE__ */ jsx(Onboarding, {});
			break;
		case "stats":
			page = /* @__PURE__ */ jsx(StatsPage, {});
			break;
		case "edit-stats":
			page = /* @__PURE__ */ jsx(EditStats, {});
			break;
		case "test-builder":
			page = /* @__PURE__ */ jsx(BuilderPage, { kind: "test" });
			break;
		case "college-builder":
			page = /* @__PURE__ */ jsx(BuilderPage, { kind: "college" });
			break;
		case "tracker":
			page = /* @__PURE__ */ jsx(TrackerPage, {});
			break;
		case "forum":
			page = /* @__PURE__ */ jsx(ForumPage, {});
			break;
		case "points":
			page = /* @__PURE__ */ jsx(PointsPage, {});
			break;
		case "account":
			page = /* @__PURE__ */ jsx(AccountPage, {});
			break;
		case "privacy":
			page = /* @__PURE__ */ jsx(LegalPage, { type: "privacy" });
			break;
		case "terms":
			page = /* @__PURE__ */ jsx(LegalPage, { type: "terms" });
			break;
		case "ai-sat-prep":
			page = /* @__PURE__ */ jsx(ProductPage, { kind: "ai-sat-prep" });
			break;
		case "sat-prep":
			page = /* @__PURE__ */ jsx(ProductPage, { kind: "sat-prep" });
			break;
		case "act-prep":
			page = /* @__PURE__ */ jsx(ProductPage, { kind: "act-prep" });
			break;
		case "college-planning":
			page = /* @__PURE__ */ jsx(ProductPage, { kind: "college-planning" });
			break;
		case "article":
			page = /* @__PURE__ */ jsx(ArticlePage, {});
			break;
		default: page = /* @__PURE__ */ jsx(Landing, {});
	}
	return /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx(Toaster, {
		position: "bottom-right",
		mobileOffset: 16,
		offset: 24,
		closeButton: true,
		theme: "light",
		toastOptions: { duration: 4200 }
	}), page] });
}
//#endregion
//#region frontend/src/entry-server.jsx
function render(page, data = {}) {
	setBoot({
		page,
		data
	});
	return renderToString(/* @__PURE__ */ jsx(App, {}));
}
//#endregion
export { boot as i, Starfield as n, api as r, render, AppShell as t };
