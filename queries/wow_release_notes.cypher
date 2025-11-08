// Markdown bullets for quick release notes
MATCH (c:Capsule)
RETURN '- **' + c.identifier + '** - ' + coalesce(c.title,'') AS md
ORDER BY md;
