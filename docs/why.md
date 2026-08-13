# Why a compiler, not a prompt

ASD-STE100 Simplified Technical English is a controlled language. Aerospace
maintenance manuals use it so a tired reader who is not a native English
speaker cannot misread an instruction. Issue 9 is dated 15 January 2025. The
standard is a free download at [asd-ste100.org](https://www.asd-ste100.org/).
It is an EU trademark of ASD. OneRead is unofficial.

A language model does the opposite of STE by default. It rotates synonyms so
the prose does not repeat. It hedges with should, may, and could. It puts the
condition after the command. It writes 40-word sentences. Those habits are
rewarded in training. They are punished in a hangar, an on-call rotation, and
an agent tool description.

A prompt can ask the model to stop. The model will try. The next call will
drift. A compiler does not try. It type-checks. It emits an artifact a CI job
can fail.

That is the job OneRead takes. The skill adapter still exists, because a model
must rewrite what a regex cannot. The compiler is the gate behind the skill.

By the end of Issue 8, 64% of registered STE users were outside aerospace and
defense (stated in the OneRead skill notes, sourced from public STEMG
commentary on Issue 8). Computer science, industry, language services, and
academia are listed as current uses on the official site.

Do not apply STE to marketing, brand, or social posts. It deletes persuasion
on purpose.
