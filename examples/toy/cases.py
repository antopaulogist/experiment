# A pool to split before the run, plus phrases that must stay as said.
SCORED = [
    ("see you at four pm", "see you at 4pm"),
    ("the call is at nine am", "the call is at 9am"),
    ("let's say four thirty pm", "let's say 4:30pm"),
    ("about half nine", "about 9:30"),
    ("quarter past six works", "6:15 works"),
    ("quarter to six", "5:45"),
    ("at four o'clock", "at 4:00"),
    ("meet at 4 p.m.", "meet at 4pm"),
    ("meet at 4.30pm", "meet at 4:30pm"),
    ("half past four", "4:30"),
    ("by ten am tomorrow", "by 10am tomorrow"),
    ("eleven fifteen am", "11:15am"),
    ("arrive at two pm", "arrive at 2pm"),
    ("leave at eight am", "leave at 8am"),
    ("meet at five thirty pm", "meet at 5:30pm"),
    ("about half seven", "about 7:30"),
    ("quarter past three works", "3:15 works"),
    ("quarter to eight", "7:45"),
    ("at six o'clock", "at 6:00"),
    ("meet at 2 p.m.", "meet at 2pm"),
    ("meet at 6.30pm", "meet at 6:30pm"),
    ("half past two", "2:30"),
    ("by three am tomorrow", "by 3am tomorrow"),
    ("seven fifteen am", "7:15am"),
]
KEEP = [
    "cut it in half four ways",
    "no one said five to six people",
    "give me a second",
    "first of all",
]

if __name__ == '__main__':
    import json
    for n, (text, answer) in enumerate(SCORED, 1):
        print(json.dumps({'id': str(n), 'text': text, 'answer': answer}))
