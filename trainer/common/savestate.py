from typing import Dict


def load(filepath: str) -> Dict[str, str]:
    state: Dict[str, str] = {}
    with open(filepath, 'r') as f:
        for line in f.readlines():
            filename, _, classification = line.strip().partition(' ')
            state[filename] = classification
    return state


def save(state: Dict[str, str], filepath: str) -> None:
    with open(filepath, 'w') as f:
        f.writelines(f'{filename} {classification}' for filename,
                     _, classification in state.items())
