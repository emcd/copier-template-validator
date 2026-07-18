Change the rendered ``ValidationResult`` item count from
``X/Y generated`` to ``X of Y generated``. The new phrasing
reads unambiguously as "X items were generated out of Y
attempted", rather than a numerator/denominator ratio whose
meaning the reader had to infer. The format also reads
correctly when ``items_generated`` differs from
``items_attempted``; the underlying dataclass always supported
the divergent case but the previous output did not distinguish
it.
