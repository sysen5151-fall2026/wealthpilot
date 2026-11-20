# F.6 explanation deployment measurements

On November 20, 2026, the WealthPilot component spike used checkout `61989ab`, the existing synthetic recommendations fixture, and the approved Explanation Rules. Timing began at F.6.1 entry and ended when F.6.2 returned its presentation object. The test used an Apple Silicon Mac with Python 3.13.4. Browser rendering, network transport to a browser and human comprehension were outside the test.

| Candidate | Observation | Scope |
| --- | --- | --- |
| Deterministic template | p95 0.0959 ms, n=100 | Same synthetic fixture repeated in-process on checkout `f981421` |
| Ollama 0.34.2 with Llama 3.2 | 0 model responses in 6 GPU attempts | Metal initialization failed on the tested host. Every request used the template. |
| Bundled llama-server, Llama 3.2, CPU | 6 model responses used in 6 trials. 0 of 6 within the 2.0 s budget. | Loopback, 4 CPU threads, context 4096, one repeated synthetic scenario |
| Hosted API | No measured value | No provider or approved external payload was in place for the pilot |

CPU seconds in run order: **18.6812, 10.3974, 10.9139, 13.3682, 10.2908, 8.6377**. The allocation preserved the expected 60% US Stocks and 40% Bonds in the reviewed presentation object on every run. The 6 accepted outputs are evidence of adapter operation on this fixture. The sample is too small and narrow to establish production latency or independent factual fidelity.

The 2.0 s threshold comes from CS6.2.1 in the Innoslate model. The [Ollama compatibility reference](https://docs.ollama.com/api/openai-compatibility) describes the local OpenAI-compatible interface. No external model calls were made during this spike.
