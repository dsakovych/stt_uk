letter_mapping = {"я": "й а", "ю": "й у", "є": "й е", "ї": "й і"}
# uk_letters = "абвгґдеєжзиійклмнопрстуфхцчшщьюя"
uk_letters = ['а', 'б', 'в', 'г', 'ґ', 'д', 'е', 'є', 'ж', 'з', 'и', 'і', 'ї', 'й', 'к', 'л', 'м',
              'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ь', 'ю', 'я']


def word2phonemes(word):
    graphemes = []
    for index, letter in enumerate(word):
        if letter in letter_mapping:
            if index == 0 or word[index-1] == '`' or word[index-1] in letter_mapping:
                graphemes.append(letter_mapping.get(letter))
            else:
                graphemes[-1] += "'" + letter_mapping.get(letter)[-1]
        elif letter == '`':
            continue
        elif letter == 'ь':
            graphemes[-1] += "'"
        else:
            graphemes.append(letter)

    return " ".join(graphemes)


if __name__ == '__main__':
    words = ["дивний", 'яєшня', "їжак", "подивись", 'юнайтед', 'дьоготь']
    for w in words:
        print(word2phonemes(w))
