y_vowel_letters = {"я": "й а", "ю": "й у", "є": "й е", "ї": "й і"}
vowel_letters = {"а", "о", "у", "е", "і", "и"}
only_hard = {}

# uk_letters = "абвгґдеєжзиійклмнопрстуфхцчшщьюя"
uk_letters = ['а', 'б', 'в', 'г', 'ґ', 'д', 'е', 'є', 'ж', 'з', 'и', 'і', 'ї', 'й', 'к', 'л', 'м',
              'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ь', 'ю', 'я']


def word2phonemes(word):
    graphemes = []
    try:
        for index, letter in enumerate(word):
            if letter in y_vowel_letters:
                if index == 0 or word[index - 1] == '`' \
                              or word[index - 1] in y_vowel_letters \
                              or word[index - 1] in vowel_letters:
                    graphemes.append(y_vowel_letters.get(letter))
                else:
                    graphemes[-1] += "' " + y_vowel_letters.get(letter)[-1]
            elif letter == '`':
                continue
            elif letter == 'ь':
                graphemes[-1] += "'"
            elif letter == 'і':
                if index == 0:
                    graphemes.append(letter)
                else:
                    graphemes[-1] += "' " + letter
            elif letter == 'щ':
                graphemes.append("ш")
                graphemes.append("ч")
            else:
                graphemes.append(letter)

        return " ".join(graphemes)
    except Exception as e:
        print(f"failed to convert: {word}")


if __name__ == '__main__':
    words = ["дивний", 'яєшня', "їжак", "подивись", 'юнайтед', 'дьоготь', "є", "каденції"]
    for w in words:
        print(word2phonemes(w))
