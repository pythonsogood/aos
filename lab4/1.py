text = input("Enter a sentence: ")

words = tuple(word for word in text.split(" ") if len(word.strip()) > 0)

print(f"Word count: {len(words)}")
