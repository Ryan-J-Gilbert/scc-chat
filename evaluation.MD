DEPRECATED

We need to make sure the chatbot is providing accurate answers for SCC specific questions.

In evaluation.json, there are a few prompts with what we should and should not expect.  
For each question, we have an associated should_query, good_keywords, and bad_keywords.  
We can loop throught the prompts, ask the question, see if querying happened, see if the response captures the right keywords and not the wrong ones.  
We can also use another LLM to judge output based on: relevance, hallucination presence, completeness.

Some issues can be resolved with better system prompt, maybe we can also add some prompt preprocessing too.  
E.g.: 
"how do i run a job with a lot of memory"  
->  
"how do i run a batch job with a lot of memory on the scc?"

Evaluation questions can be expanded by asking RCS team, seeing what types of questions come in when released live